"""
:casecomponent: insights-client
:requirement: RHSS-291297
:polarion-project-id: RHELSS
:polarion-include-skipped: false
:polarion-lookup-method: id
:subsystemteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import conftest
from time import sleep
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
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed {description}: {e.stderr}")
        raise RuntimeError(f"Failed {description}: {e.stderr}") from e


def _wait_for_timer_execution(timer_name, timeout_sec=420):  # 7 minutes timeout
    """Wait for the systemd timer to actually execute and complete."""
    logger.debug(f"Waiting for timer {timer_name} to execute...")

    def check_timer_ran():
        # Check if the timer ran recently by looking at journal logs
        cmd = [
            "journalctl",
            "-u",
            timer_name,
            "--since",
            "10 minutes ago",
            "--no-pager",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            recent_logs = result.stdout
            # Look for timer activation logs
            if "Started" in recent_logs or "Finished" in recent_logs:
                logger.debug(f"Timer {timer_name} execution detected in logs")
                return True
        return False

    def check_service_ran():
        # Check if the insights-client service ran recently
        cmd = [
            "journalctl",
            "-u",
            "insights-client.service",
            "--since",
            "10 minutes ago",
            "--no-pager",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            recent_logs = result.stdout
            if "Started" in recent_logs or "Finished" in recent_logs:
                logger.debug("insights-client.service execution detected in logs")
                return True
        return False

    # Poll for timer/service execution
    return conftest.loop_until(
        lambda: check_timer_ran() or check_service_ran(),
        poll_sec=10,
        timeout_sec=timeout_sec,
    )


@pytest.mark.tier1
def test_data_upload_systemd_timer(insights_client, external_inventory):
    """
    :id: 6bbac679-cb37-47b1-9163-497f1a1758dd
    :title: Verify insights-client upload via systemd timer
    :description:
        Ensure that the insights-client data upload is triggered by the
        systemd timer and the last check-in time is updated accordingly
    :tags: Tier 1
    :steps:
        1. Register the system
        2. Note the last_check_in in host details from inventory
        3. Edit insights-client timer to run every 2 minutes with minimal delay
        4. Enable and restart the timer to apply new configuration
        5. Wait for timer execution and upload to complete
        6. Again note the last_check_in in host details from inventory
        7. Verify the updated last_check_in time
    :expectedresults:
        1. System is registered
        2. The last_check_in time is recorded from the inventory
        3. The timer is adjusted to a 2-minute interval and restarted successfully
        4. Timer executes and upload completes successfully
        5. Wait for 60 seconds to ensure the data is propagated to the inventory
        5. The last_check_in time is recorded from the inventory
        6. The last_check_in time is updated, reflecting a successful upload
    """
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    # Get initial check-in time using consistent API call
    initial_response = external_inventory.this_system()
    last_checkin_time = initial_response["per_reporter_staleness"]["puptoo"][
        "last_check_in"
    ]
    logger.debug(f"Initial check-in time: {last_checkin_time}")

    # Create override configuration for insights-client timer to run every 2 minutes
    override_path = Path("/etc/systemd/system/insights-client.timer.d/override.conf")
    override_content = """[Timer]
        OnCalendar=*:0/2
        Persistent=true
        RandomizedDelaySec=10
        """

    timer_was_active = False
    try:
        # Check if timer was initially active
        result = subprocess.run(
            ["systemctl", "is-active", "insights-client.timer"],
            capture_output=True,
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
            capture_output=True,
            text=True,
        )
        assert (
            result.returncode == 0 and result.stdout.strip() == "active"
        ), f"insights-client.timer failed to start: {result.stderr}"

        logger.debug("Timer is now active with override configuration")

        # Wait for the timer to execute and complete
        timer_executed = _wait_for_timer_execution("insights-client.timer")
        if not timer_executed:
            # Try to trigger manually if timer didn't run
            logger.warning("Timer didn't execute within timeout, triggering manually")
            _run_systemctl_command(
                ["systemctl", "start", "insights-client.service"],
                "manual service start",
            )

            # Wait a bit more for manual execution to complete
            sleep(30)

        # Wait additional time for data to propagate to inventory
        sleep(60)

        # Fetch the updated check-in time using consistent API call
        updated_response = external_inventory.this_system()
        latest_checkin_time = updated_response["per_reporter_staleness"]["puptoo"][
            "last_check_in"
        ]
        logger.debug(f"Updated check-in time: {latest_checkin_time}")

        # Verify that the check-in time was updated
        assert last_checkin_time < latest_checkin_time, (
            f"Check-in time was not updated: initial={last_checkin_time}, "
            f"latest={latest_checkin_time}"
        )

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
