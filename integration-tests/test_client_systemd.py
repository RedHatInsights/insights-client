"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import datetime
import logging
import re
import subprocess
import tempfile
from pathlib import Path

import pytest
from pytest_client_tools.util import loop_until
from conftest import wait_for_services_to_finish
from constants import INSIGHTS_CLIENT_LASTUPLOAD_FILE, INSIGHTS_CLIENT_LOG_FILE

logger = logging.getLogger(__name__)
pytestmark = pytest.mark.usefixtures("register_subman")


def _run_systemctl_command(cmd, description="systemctl operation"):
    """Helper function to run systemctl commands with proper error handling."""
    logger.debug(f"Running systemctl command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed {description}: {e.stderr}")
        raise RuntimeError(f"Failed {description}: {e.stderr}") from e


def _last_upload_state(last_upload_file):
    """Return the current state of the last-upload marker, if it exists."""
    try:
        stat = last_upload_file.stat()
        return stat.st_mtime_ns, stat.st_size, last_upload_file.read_bytes()
    except FileNotFoundError:
        return None


def _is_systemd_unit_active(unit):
    return (
        subprocess.run(
            ["systemctl", "is-active", "--quiet", unit],
            check=False,
        ).returncode
        == 0
    )


def _wait_for_timer_execution_by_lastupload(interval_minutes=3, additional_wait_sec=120):
    """Wait for the systemd timer to complete an upload."""
    last_upload_file = Path(INSIGHTS_CLIENT_LASTUPLOAD_FILE)

    # Persistent=true can trigger an immediate catch-up run when the timer is
    # restarted. Drain that run before taking the baseline, otherwise the
    # catch-up upload would be mistaken for the next scheduled run.
    wait_for_services_to_finish()

    baseline = _last_upload_state(last_upload_file)
    logger.debug("Recorded .lastupload baseline: %s", baseline is not None)

    # Wait for the timer interval plus additional buffer time. The timer keeps
    # the default AccuracySec=1min, so allow enough headroom for the next run.
    wait_time = (interval_minutes * 60) + additional_wait_sec
    logger.debug(f"Waiting {wait_time} seconds for .lastupload to change...")

    # A successful upload updates .lastupload. Unlike log-file creation, this
    # does not require deleting a file that an insights_core_t process may use.
    return loop_until(
        lambda: (
            (current := _last_upload_state(last_upload_file)) is not None and current != baseline
        ),
        poll_sec=10,
        timeout_sec=wait_time,
    )


@pytest.mark.tier1
def test_data_upload_systemd_timer(insights_client):
    """
    :id: 6bbac679-cb37-47b1-9163-497f1a1758dd
    :title: Verify insights-client upload is triggered by the systemd timer
    :description:
        Ensure that the insights-client systemd timer triggers a successful
        upload by verifying that the last-upload marker changes.
    :reference: https://issues.redhat.com/browse/CCT-1557
    :tags: Tier 1
    :steps:
        1. Register the system
        2. Edit insights-client timer to run every 3 minutes with minimal delay
        3. Enable and restart the timer to apply new configuration
        4. Wait for any immediate persistent catch-up run to finish and record
           the current last-upload marker
        5. Wait for the next scheduled timer run to complete
        6. Verify that the last-upload marker changed
    :expectedresults:
        1. System is registered successfully
        2. The timer is adjusted to a 3-minute interval and restarted successfully
        3. Timer is active with the new configuration
        4. The current last-upload marker is recorded after any catch-up run
        5. The timer triggers an upload within the expected timeframe
        6. The last-upload marker changes, confirming a successful upload
    """
    insights_client.register()
    assert loop_until(lambda: insights_client.is_registered)

    # Create override configuration for insights-client timer to run every 3 minutes
    override_path = Path("/etc/systemd/system/insights-client.timer.d/override.conf")
    override_content = """[Timer]
        OnCalendar=*:0/3
        Persistent=true
        RandomizedDelaySec=5
        """

    # Check if timer was initially active
    _run_systemctl_command(
        ["systemctl", "is-active", "insights-client.timer"], "check timer status"
    )
    logger.debug("Timer was initially active")

    # Create override directory and configuration
    override_path.parent.mkdir(parents=True, exist_ok=True)
    override_path.write_text(override_content)
    logger.debug(f"Created timer override at {override_path}")

    # Reload systemd configuration
    _run_systemctl_command(["systemctl", "daemon-reload"], "daemon reload")

    # Enable and restart the timer to apply new configuration
    _run_systemctl_command(["systemctl", "enable", "insights-client.timer"], "timer enable")
    _run_systemctl_command(["systemctl", "restart", "insights-client.timer"], "timer restart")

    # Verify timer is now active
    _run_systemctl_command(
        ["systemctl", "is-active", "insights-client.timer"],
        "verify timer is active",
    )

    logger.debug("Timer is now active with override configuration")

    try:
        # Wait for the timer to execute by monitoring the last-upload marker
        timer_executed = _wait_for_timer_execution_by_lastupload(interval_minutes=3)

        assert timer_executed, (
            "Timer did not complete an upload within the expected timeframe. "
            "The .lastupload marker did not change."
        )

        logger.debug("Timer execution confirmed - .lastupload was updated")

    finally:
        # Remove the temporary timer override and stop the timer to prevent another run
        _run_systemctl_command(["systemctl", "revert", "insights-client.timer"], "timer revert")
        _run_systemctl_command(["systemctl", "daemon-reload"], "daemon reload after revert")

        # Ensure timer is stopped after revert
        _run_systemctl_command(["systemctl", "stop", "insights-client.timer"], "timer stop")

        # Ensure override file is removed
        override_path.unlink(missing_ok=True)
        logger.debug("Removed override configuration file")

        # Clean up log file if it exists
        log_file = Path(INSIGHTS_CLIENT_LOG_FILE)
        log_file.unlink(missing_ok=True)
        logger.debug("Cleaned up insights-client log file")


@pytest.mark.tier1
def test_insights_client_service_completes_without_seccomp_kills(insights_client):
    """
    :id: 10b4efb4-4b26-4af7-91c3-45da9be513fd
    :title: Verify Insights collection succeeds under the systemd sandbox
    :description:
        Run the default collection through insights-client.service and verify
        that it completes successfully without seccomp killing a collector.
    :tags: Tier 1
    :steps:
        1. Register insights-client
        2. Stop the timer and disable service restarts for this invocation
        3. Start insights-client.service and wait for it to exit
        4. Verify the service exits successfully and produces no SECCOMP events
    :expectedresults:
        1. The client is registered
        2. The service runs once with its normal command and sandbox settings
        3. The service exits with Result=success and ExecMainStatus=0
        4. No seccomp-denied syscall terminates collection processes
    """
    service = "insights-client.service"
    timer = "insights-client.timer"

    insights_client.register()
    assert loop_until(lambda: insights_client.is_registered)

    timer_was_active = _is_systemd_unit_active(timer)
    override_path = None
    override_dir = Path("/run/systemd/system/insights-client.service.d")

    try:
        _run_systemctl_command(["systemctl", "stop", timer], "stop client timer")
        _run_systemctl_command(["systemctl", "stop", service], "stop client service")

        override_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            prefix="zz-insights-client-integration-",
            suffix=".conf",
            dir=override_dir,
            delete=False,
        ) as override_file:
            override_file.write("[Service]\nRestart=no\n")
            override_path = Path(override_file.name)

        _run_systemctl_command(["systemctl", "daemon-reload"], "load service override")
        _run_systemctl_command(
            ["systemctl", "reset-failed", service], "reset previous service result"
        )

        start_time = datetime.datetime.now()
        start_result = subprocess.run(
            ["systemctl", "start", "--wait", service],
            capture_output=True,
            text=True,
            check=False,
        )
        end_time = datetime.datetime.now()

        status_result = _run_systemctl_command(
            [
                "systemctl",
                "show",
                service,
                "--property=Result",
                "--property=ExecMainStatus",
            ],
            "read service result",
        )
        service_status = dict(
            line.split("=", 1) for line in status_result.stdout.splitlines() if "=" in line
        )

        audit_result = subprocess.run(
            ["ausearch", "-m", "SECCOMP", "-ts", "boot", "--raw"],
            capture_output=True,
            text=True,
            check=False,
        )
        seccomp_records = [
            line for line in audit_result.stdout.splitlines() if line.startswith("type=SECCOMP ")
        ]
        seccomp_events = []
        for record in seccomp_records:
            match = re.search(r"msg=audit\((\d+(?:\.\d+)?):", record)
            assert match, f"Could not parse seccomp audit record: {record}"
            event_time = float(match.group(1))
            if start_time.timestamp() <= event_time <= end_time.timestamp():
                seccomp_events.append(record)

        assert start_result.returncode == 0, (
            "systemctl start --wait failed:\n"
            f"stdout: {start_result.stdout}\nstderr: {start_result.stderr}"
        )
        assert service_status.get("Result") == "success", service_status
        assert service_status.get("ExecMainStatus") == "0", service_status
        assert audit_result.returncode in (
            0,
            1,
        ), f"ausearch failed: {audit_result.stderr or audit_result.stdout}"
        assert (
            not seccomp_events
        ), "Seccomp events occurred while insights-client.service was running:\n" + "\n".join(
            seccomp_events
        )
    finally:
        subprocess.run(["systemctl", "stop", service], check=False)
        if override_path is not None:
            override_path.unlink(missing_ok=True)
        subprocess.run(["systemctl", "daemon-reload"], check=False)
        subprocess.run(["systemctl", "reset-failed", service], check=False)
        if timer_was_active:
            _run_systemctl_command(["systemctl", "start", timer], "restore client timer")
