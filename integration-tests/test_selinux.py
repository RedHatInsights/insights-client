"""
:casecomponent: insights-client
:requirement: RHSS-291816
:subsystemteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import re
import subprocess
import time
import pytest
from contextlib import contextmanager
from pytest_client_tools.util import loop_until
from datetime import datetime

pytestmark = pytest.mark.usefixtures("register_subman")


# Skip entire test file if SELinux is disabled
def _get_selinux_mode():
    """Get current SELinux mode (Enforcing, Permissive, or Disabled)."""
    try:
        result = subprocess.run(
            ["getenforce"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "Disabled"


# Check if SELinux is disabled and skip all tests in this module
if _get_selinux_mode() == "Disabled":
    pytest.skip("SELinux is disabled on this system", allow_module_level=True)


def _get_current_context():
    """Get current SELinux context by reading /proc/self/attr/current.
    This uses the kernel interface directly.
    """
    with open("/proc/self/attr/current", "r") as f:
        context = f.read().strip()
        # Remove null bytes that may be present in the file
        return context.replace("\x00", "")


def _format_audit_time(timestamp):
    """Convert timestamp to audit log format."""
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp).strftime("%m/%d/%Y %H:%M:%S").split()
    return timestamp or "today"


def _check_denials_with_ausearch(start_time, end_time=None):
    # Check for denials using ausearch command.
    cmd = [
        "ausearch",
        "--message",
        "AVC",
        "--comm",
        "insights-client",
        "--start",
    ] + _format_audit_time(start_time)
    if end_time:
        cmd.extend(["--end"] + _format_audit_time(end_time))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
    return result.stdout.strip() or None


def _parse_execve_event_block(event_lines):
    """
    Parse a block of audit lines (one event) to extract process info.
    Correlates SYSCALL (context) with EXECVE (full arguments).
    """
    # Join lines to make searching easier, or iterate
    full_text = "\n".join(event_lines)

    # 1. Extract contexts from SYSCALL
    # scontext = subject context (parent process that executed)
    scontext_match = re.search(r"(?:subj|scontext)=([^\s]+)", full_text)
    if not scontext_match:
        return None
    scontext = scontext_match.group(1)

    # tcontext = target context (file being executed)
    # newcontext = actual running context if setexeccon was used
    newcontext_match = re.search(r"newcontext=([^\s]+)", full_text)
    tcontext_match = re.search(r"tcontext=([^\s]+)", full_text)

    # Running context is newcontext if setexeccon was used, otherwise tcontext
    if newcontext_match:
        running_context = newcontext_match.group(1)
    elif tcontext_match:
        running_context = tcontext_match.group(1)
    else:
        # Fallback to scontext if neither found (shouldn't happen normally)
        running_context = scontext

    # 2. Extract Command/Arguments from EXECVE
    if "type=EXECVE" not in full_text:
        return None

    # Extract all arguments to reconstruct the command roughly
    args = re.findall(r'a\d+=(?:"([^"]+)"|([^\s]+))', full_text)
    cmd_args = [x[0] or x[1] for x in args]
    cmd_string = " ".join(cmd_args)

    # 3. Filter: Is this the process we care about?
    # We only care if the arguments mention insights-client structure
    target_markers = ["insights-client", "insights_client", "insights-core", "run.py"]
    if not any(marker in cmd_string for marker in target_markers):
        return None
    # Comm is usually the base command (first arg or explicit comm field)
    comm_match = re.search(r'comm="([^"]+)"', full_text)
    comm = (
        comm_match.group(1) if comm_match else (cmd_args[0] if cmd_args else "unknown")
    )
    # Return format: (comm_name, source_context, running_context)
    return (comm, scontext, running_context)


def _check_process_contexts_from_audit(start_time, end_time=None):
    """Check SELinux contexts of executed processes from audit logs.
    Groups lines by event ID to correlate EXECVE arguments with SYSCALL context.
    """
    contexts = []

    # Prepare ausearch command
    # Note: We search for both SYSCALL and EXECVE to ensure we get the full block
    cmd = [
        "ausearch",
        "--message",
        "SYSCALL,EXECVE",
        "--start",
    ] + _format_audit_time(start_time)
    if end_time:
        cmd.extend(["--end"] + _format_audit_time(end_time))

    # Helper to process a block of lines
    def process_block(lines):
        if not lines:
            return
        parsed = _parse_execve_event_block(lines)
        if parsed:
            contexts.append(parsed)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
    if result.returncode == 0 and result.stdout:
        current_event = []
        for line in result.stdout.splitlines():
            if line.strip() == "----":
                process_block(current_event)
                current_event = []
            else:
                current_event.append(line)
        process_block(current_event)  # Process the last block
    return contexts


# Context managers
@contextmanager
def _selinux_mode(mode):
    # Context manager to set SELinux mode and restore original mode on exit.
    original_mode = _get_selinux_mode()
    try:
        subprocess.run(["setenforce", mode], check=True)
    except FileNotFoundError:
        pytest.skip(reason="setenforce command not available - SELinux not installed")
    except subprocess.CalledProcessError as e:
        pytest.skip(reason=f"Failed to set SELinux mode to {mode}: {e}")

    try:
        yield
    finally:
        # Restore original mode
        if original_mode != "Disabled":
            try:
                subprocess.run(["setenforce", original_mode], check=True)
            except subprocess.CalledProcessError:
                # Log but don't fail if restore fails
                pass


# Classes
class SELinuxDenialsChecker:
    """Context manager for checking SELinux denials during a time period.
    This context manager automatically tracks start_time and end_time,
    removing the need for manual time tracking in tests.
    """

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        return False

    def get_denials(self):
        # Get AVC denials that occurred during the context manager period.
        return _check_denials_with_ausearch(self.start_time, self.end_time)

    def get_process_contexts(self):
        # Get process contexts from execve events during the context manager period.
        return _check_process_contexts_from_audit(self.start_time, self.end_time)


@pytest.mark.tier2
def test_register_unconfined_t_no_context_change(insights_client):
    """
    :id: 91c9c37f-b954-4fc4-84da-a4a2a9dbee9d
    :title: Test insights-client --register runs in unconfined_t without context change
    :description:
        This test verifies that when running insights-client --register as root
        in unconfined_t SELinux context with SELinux enforcing mode, the insights-core
        code executes in unconfined_t context without any SELinux context change
        and without any SELinux denials.
    :tags: Tier 1
    :reference: https://issues.redhat.com/browse/CCT-1717
    :steps:
        1. Register system using subscription-manager (already done by fixture)
        2. Set SELinux to enforcing mode (using context manager)
        3. Verify current context is unconfined_t
        4. Run insights-client --register as root in unconfined_t context
        5. Verify registration succeeded
        6. Check audit logs for process execution contexts (SYSCALL execve events)
        7. Check audit logs for SELinux AVC denials
    :expectedresults:
        1. System is registered (handled by register_subman fixture)
        2. SELinux is set to enforcing mode and will be restored automatically
        3. Current context is confirmed as unconfined_t
        4. insights-client --register completes successfully
        5. Registration status confirms system is registered
        6. All insights-client and insights-core processes executed in
           unconfined_t context
        7. No SELinux AVC denials found in audit logs
    """
    with _selinux_mode("Enforcing"):
        context = _get_current_context()
        assert "unconfined_t" in context, f"Expected unconfined_t, got: {context}"

        with SELinuxDenialsChecker() as checker:
            result = insights_client.run("--register", selinux_context=None)
            assert result.returncode == 0, f"Registration failed: {result.returncode}"

            # Verify registration
            def check_registered():
                status = insights_client.run(
                    "--status", check=False, selinux_context=None
                )
                return status.returncode == 0 and any(
                    i in status.stdout
                    for i in ["This host is registered", "Registered"]
                )

            assert loop_until(check_registered)

        # Verify process contexts from audit logs
        for proc_name, scontext, running_context in checker.get_process_contexts():
            if any(
                x in proc_name for x in ["insights-core", "insights_client", "python"]
            ):
                if any(
                    x in running_context
                    for x in ["insights_client_t", "insights_core_t"]
                ):
                    pytest.fail(
                        f"Process {proc_name} ran in confined context "
                        f"{running_context} instead of unconfined_t. "
                        f"Found contexts: {checker.get_process_contexts()}"
                    )
                if "unconfined_t" not in scontext:
                    pytest.fail(
                        f"Process {proc_name} executed from non-unconfined "
                        f"context {scontext}. "
                        f"Found contexts: {checker.get_process_contexts()}"
                    )

        # Verify no SELinux denials
        denials = checker.get_denials()
        assert not denials, f"SELinux denials found:\n{denials}"


@pytest.mark.tier2
def test_register_unconfined_service_t_registration(insights_client):
    """
    :id: 38fb9519-a4cf-4677-a55a-d7f660a21a3e
    :title: Check registration running in unconfined_service_t context
    :description:
        This test checks that if insights --register is invoked by other (unconfined)
        service, the registrations is still successful and more strict confinement is
        not applied. This is mostly needed because insights-client is used not only
        for reporting to insights,but also to invoke other code that is shipped within
        the insights-core python library.
    :tags: Tier 2
    :reference: https://issues.redhat.com/browse/CCT-1718
    :steps:
        1. (setup) Switch system to SELinux enforcing mode
        2. As a root user run insights-client --register in unconfined_service_t
           context.
        3. Check that “insights-core” code was executed in unconfined_service_t
           context
    :expectedresults:
        1. (setup) The system is running in SELinux enforcing mode
        2. Registration is successful
        3. The insights-client (and the children processes) did not run under different
          (more confined) mode.
    """
    # Not switching explicitly to enforcing mode, the system should be already in it
    # unless someone wanted to explicitly test with permissive mode.
    with SELinuxDenialsChecker() as checker:
        subprocess.run(
            [
                "runcon",
                "system_u:system_r:unconfined_service_t:s0",
                "/bin/bash",
                "-c",
                "insights-client --register",
            ],
            check=True,
        )

    # copied from test_register_unconfined_t_no_context_change
    # and reformatted because black demanded it
    for proc_name, scontext, running_context in checker.get_process_contexts():
        if any(x in proc_name for x in ["insights-core", "insights_client", "python"]):
            if any(
                x in running_context for x in ["insights_client_t", "insights_core_t"]
            ):
                pytest.fail(
                    f"Process {proc_name} ran in confined context "
                    f"{running_context} instead of unconfined_service_t. "
                    f"Found contexts: {checker.get_process_contexts()}"
                )
            if "unconfined_service_t" not in scontext:
                pytest.fail(
                    f"Process {proc_name} executed from non-unconfined "
                    f"context {scontext}. "
                    f"Found contexts: {checker.get_process_contexts()}"
                )
