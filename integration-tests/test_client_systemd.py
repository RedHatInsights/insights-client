"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import conftest
import pytest
import subprocess
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
pytestmark = pytest.mark.usefixtures("register_subman")


def _run_systemctl_command(cmd, description="systemctl operation"):
    """Helper function to run systemctl commands with proper error handling."""
    logger.debug(f"Running systemctl command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed {description}: {e.stderr}")
        raise RuntimeError(f"Failed {description}: {e.stderr}") from e


def _wait_for_timer_execution_by_logfile(interval_minutes=3, additional_wait_sec=30):
    """Wait for the systemd timer to execute by monitoring log file creation."""
    log_file = Path("/var/log/insights-client/insights-client.log")

    # Remove existing log file to ensure we detect new execution
    if log_file.exists():
        log_file.unlink()
        logger.debug("Removed existing insights-client log file")

    # Wait for timer interval plus additional buffer time
    wait_time = (interval_minutes * 60) + additional_wait_sec
    logger.debug(f"Waiting {wait_time} seconds for timer execution...")

    # Use conftest.loop_until to check for log file recreation
    return conftest.loop_until(
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
    assert conftest.loop_until(lambda: insights_client.is_registered)

    # Create override configuration for insights-client timer to run every 3 minutes
    override_path = Path("/etc/systemd/system/insights-client.timer.d/override.conf")
    override_content = """[Timer]
        OnCalendar=*:0/3
        Persistent=true
        RandomizedDelaySec=5
        """

    timer_was_active = False
    try:
        # Check if timer was initially active
        result = subprocess.run(
            ["systemctl", "is-active", "insights-client.timer"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        timer_was_active = result.returncode == 0 and result.stdout.strip() == "active"
        logger.debug(f"Timer was initially active: {timer_was_active}")

        # Create override directory and configuration
        override_path.parent.mkdir(parents=True, exist_ok=True)
        override_path.write_text(override_content)
        logger.debug(f"Created timer override at {override_path}")

        # Reload systemd configuration
        _run_systemctl_command(["systemctl", "daemon-reload"], "daemon reload")

        # Enable and start/restart the timer to apply new configuration
        _run_systemctl_command(
            ["systemctl", "enable", "insights-client.timer"], "timer enable"
        )

        if timer_was_active:
            _run_systemctl_command(
                ["systemctl", "restart", "insights-client.timer"], "timer restart"
            )
        else:
            _run_systemctl_command(
                ["systemctl", "start", "insights-client.timer"], "timer start"
            )

        # Verify timer is now active
        result = subprocess.run(
            ["systemctl", "is-active", "insights-client.timer"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert (
            result.returncode == 0 and result.stdout.strip() == "active"
        ), f"insights-client.timer failed to start: {result.stderr}"

        logger.debug("Timer is now active with override configuration")

        # Wait for the timer to execute by monitoring log file creation
        timer_executed = _wait_for_timer_execution_by_logfile(interval_minutes=3)

        assert timer_executed, (
            "Timer did not execute within expected timeframe. "
            "Log file was not recreated, indicating upload did not occur."
        )

        logger.debug("Timer execution confirmed - log file was recreated")

    finally:
        # Clean up: revert timer configuration and restore original state
        try:
            _run_systemctl_command(
                ["systemctl", "revert", "insights-client.timer"], "timer revert"
            )
            _run_systemctl_command(
                ["systemctl", "daemon-reload"], "daemon reload after revert"
            )

            # Restore original timer state
            if timer_was_active:
                _run_systemctl_command(
                    ["systemctl", "start", "insights-client.timer"], "timer restore"
                )
            else:
                _run_systemctl_command(
                    ["systemctl", "stop", "insights-client.timer"], "timer stop"
                )
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

        # Ensure override file is removed
        try:
            if override_path.exists():
                override_path.unlink()
                logger.debug("Removed override configuration file")
        except Exception as e:
            logger.error(f"Error removing override file: {e}")

        # Clean up log file if it exists
        try:
            log_file = Path("/var/log/insights-client/insights-client.log")
            if log_file.exists():
                log_file.unlink()
                logger.debug("Cleaned up insights-client log file")
        except Exception as e:
            logger.error(f"Error removing log file: {e}")
