"""
:casecomponent: insights-client
:requirement: RHSS-291816
:subsystemteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import re
import subprocess
import pytest
from contextlib import contextmanager
from pytest_client_tools.util import loop_until

from selinux import SELinuxAVCChecker
from constants import REGISTERED_FILE

pytestmark = pytest.mark.usefixtures("register_subman")


# Skip entire test file if SELinux is disabled
def _get_selinux_mode():
    """Get current SELinux mode (Enforcing, Permissive, or Disabled)."""
    try:
        result = subprocess.run(["getenforce"], capture_output=True, text=True, check=True)
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
    :tags: Tier 2
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

        with SELinuxAVCChecker() as checker:
            result = insights_client.run("--register", selinux_context=None)
            assert result.returncode == 0, f"Registration failed: {result.returncode}"

            # Verify registration
            def check_registered():
                status = insights_client.run("--status", check=False, selinux_context=None)
                return status.returncode == 0 and any(
                    i in status.stdout for i in ["This host is registered", "Registered"]
                )

            assert loop_until(check_registered)

        # Verify process contexts from audit logs
        for proc_name, scontext, running_context in checker.get_process_contexts():
            if any(x in proc_name for x in ["insights-core", "insights_client", "python"]):
                if any(x in running_context for x in ["insights_client_t", "insights_core_t"]):
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
    with SELinuxAVCChecker() as checker:
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
            if any(x in running_context for x in ["insights_client_t", "insights_core_t"]):
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


@pytest.mark.tier2
def test_selinux_core_context(insights_client, check_avcs):
    f"""
    :id: 27163bb4-ab05-421b-b471-b2ba655f3773
    :title: insights-client executed by insights-client.service or
        other service that transitions to insights_client_t
    :description:
        Check that the core code is executed with correct context (insights_core_t) if
        insights-client is executed under insights_client_t context.
        Check this by invoking unregister code that removes .registered file,
        and have that file with file context that insights_core_t process
        should not be allowed to remove.
    :tags: Tier 2
    :reference: https://issues.redhat.com/browse/CCT-1719
    :steps:
        1. Register system using subscription-manager and insights-client (setup)
        2. Change SELinux context type of '{REGISTERED_FILE}' to "shadow_t" (setup)
        3. Switch system to SELinux permissive mode (setup)
        4. Run insights-client --unregister in insights_client_t SELinux context
        5. Look for denial about removing '{REGISTERED_FILE}' by
           a process with SELinux context insights_core_t
    :expectedresults:
        1. System is registered (setup)
        2. SELinux context type of the file is changed (setup)
        3. System is running in SELinux permissive mode (setup)
        4. System is successfully unregistered
        5. The SELinux AVC was hit
    """
    expected_denial_pattern = re.compile(
        r"^type=AVC .* avc:  denied  { unlink } for .* "
        r"name=\.registered .* "
        r"scontext=system_u:system_r:insights_core_t:s0 "
        r"tcontext=unconfined_u:object_r:shadow_t:s0 "
        r"tclass=file permissive=1 $",
        flags=re.MULTILINE,
    )
    check_avcs.skip_avc_re(expected_denial_pattern)
    insights_client.register(wait_for_registered=True)
    subprocess.run(["chcon", "-t", "shadow_t", REGISTERED_FILE], check=True)

    with _selinux_mode("permissive"):
        with SELinuxAVCChecker() as checker:
            status = insights_client.run("--unregister")
            assert status.returncode == 0
            assert status.stdout == "Successfully unregistered this host.\n"

    for avc in checker.get_avcs(skiplisted=False):
        if expected_denial_pattern.search(str(avc)):
            # Found the expected AVC
            break
    else:
        pytest.fail(
            "No AVC about attempting to access shadow_t file found.\n"
            "This most probably means that either the client/core process ran "
            "under incorrect SELinux context or the selinux policy is too graceful.\n"
        )
