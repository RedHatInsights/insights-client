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
from constants import INSIGHTS_CLIENT_LOG_FILE

logger = logging.getLogger(__name__)
pytestmark = pytest.mark.usefixtures("register_subman")


def _run_systemctl_command(cmd, description="systemctl operation"):
    """Helper function to run systemctl commands with proper error handling."""
    logger.debug(f"Running systemctl command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True,
        )
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed {description}: {e.stderr}")
        raise RuntimeError(f"Failed {description}: {e.stderr}") from e


def _wait_for_timer_execution_by_logfile(interval_minutes=3, additional_wait_sec=30):
    """Wait for the systemd timer to execute by monitoring log file creation."""
    log_file = Path(INSIGHTS_CLIENT_LOG_FILE)

    # Remove existing log file to ensure we detect new execution
    try:
        log_file.unlink()
        logger.debug("Removed existing insights-client log file")
    except OSError:
        logger.debug("No existing insights-client log file to remove")

    # Wait for timer interval plus additional buffer time
    wait_time = (interval_minutes * 60) + additional_wait_sec
    logger.debug(f"Waiting {wait_time} seconds for timer execution...")

    # Use loop_until to check for log file recreation
    return loop_until(
        lambda: log_file.exists(),
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
        systemd timer by verifying log file creation
    :reference: https://issues.redhat.com/browse/CCT-1557
    :tags: Tier 1
    :steps:
        1. Register the system
        2. Edit insights-client timer to run every 3 minutes with minimal delay
        3. Enable and restart the timer to apply new configuration
        4. Remove existing log file
        5. Wait for timer execution and upload to complete
        6. Verify that log file was recreated, indicating successful upload
    :expectedresults:
        1. System is registered successfully
        2. The timer is adjusted to a 3-minute interval and restarted successfully
        3. Timer is active with the new configuration
        4. Existing log file is removed successfully
        5. Timer executes and upload completes within expected timeframe
        6. Log file is recreated, confirming the timer triggered the upload
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
        # Wait for the timer to execute by monitoring log file creation
        timer_executed = _wait_for_timer_execution_by_logfile(interval_minutes=3)

        assert timer_executed, (
            "Timer did not execute within expected timeframe. "
            "Log file was not recreated, indicating upload did not occur."
        )

        logger.debug("Timer execution confirmed - log file was recreated")

    finally:
        # Clean up: revert timer configuration and restore original state
        _run_systemctl_command(["systemctl", "revert", "insights-client.timer"], "timer revert")
        _run_systemctl_command(["systemctl", "daemon-reload"], "daemon reload after revert")

        # Ensure timer is stopped after revert
        _run_systemctl_command(["systemctl", "stop", "insights-client.timer"], "timer stop")

        # Ensure override file is removed
        try:
            override_path.unlink()
            logger.debug("Removed override configuration file")
        except OSError:
            logger.debug("No override configuration file to remove")

        # Clean up log file if it exists
        log_file = Path(INSIGHTS_CLIENT_LOG_FILE)
        try:
            log_file.unlink()
            logger.debug("Cleaned up insights-client log file")
        except OSError:
            logger.debug("No insights-client log file to clean up")
