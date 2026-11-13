"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import pytest
import subprocess
from pathlib import Path
import logging
from pytest_client_tools.util import loop_until
from conftest import wait_for_services_to_finish

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


def _wait_for_timer_execution_by_lastupload(interval_minutes=3, additional_wait_sec=120):
    """Wait for the systemd timer to complete an upload."""
    last_upload_file = Path("/etc/insights-client/.lastupload")

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
    :title: Verify insights-client upload via systemd timer
    :description:
        Ensure that the insights-client data upload is triggered by the
        systemd timer by verifying the last-upload marker is updated
    :reference: https://redhat.atlassian.net/browse/CCT-1557
    :tags: Tier 1
    :steps:
        1. Register the system
        2. Edit insights-client timer to run every 3 minutes with minimal delay
        3. Enable and restart the timer to apply new configuration
        4. Wait for timer execution and upload to complete
        5. Verify that the last-upload marker was updated
    :expectedresults:
        1. System is registered successfully
        2. The timer is adjusted to a 3-minute interval and restarted successfully
        3. Timer is active with the new configuration
        4. Timer executes and upload completes within expected timeframe
        5. The last-upload marker is updated, confirming the timer triggered the upload
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
            "Timer did not execute within expected timeframe. "
            ".lastupload was not updated, indicating upload did not occur."
        )

        logger.debug("Timer execution confirmed - .lastupload was updated")

    finally:
        # Clean up: revert timer configuration and restore original state
        _run_systemctl_command(["systemctl", "revert", "insights-client.timer"], "timer revert")
        _run_systemctl_command(["systemctl", "daemon-reload"], "daemon reload after revert")

        # Ensure timer is stopped after revert
        _run_systemctl_command(["systemctl", "stop", "insights-client.timer"], "timer stop")

        # Ensure override file is removed
        override_path.unlink(missing_ok=True)
        logger.debug("Removed override configuration file")
