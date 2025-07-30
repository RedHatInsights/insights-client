"""
:component: insights-client
:requirement: RHSS-291297
:polarion-project-id: RHELSS
:polarion-include-skipped: false
:polarion-lookup-method: id
:poolteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import conftest
import pytest
import subprocess
import logging
from pathlib import Path

pytestmark = pytest.mark.usefixtures("register_subman")


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
        3. Edit insights-client timer to run every 3 minutes (24 hours is
            too long to wait for a test, 3 min appears be a decent wait)
        4. Wait for upload to finish
        5. Again note the last_check_in in host details from inventory
        6. Verify the updated last_check_in time
    :expectedresults:
        1. System is registered
        2. The last_check_in time is recorded from the inventory
        3. The timer is adjusted to a 3-minute interval and upload proceeds
            as expected.
        4. Upload is finished successfully
        5. The last_check_in time is recorded from the inventory
        6. The last_check_in time is updated, reflecting a successful upload
    """
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    machine_id = insights_client.uuid
    # fetching host details to note last_check_in time
    response = external_inventory.get(path=f"hosts?insights_id={machine_id}")
    host_staleness = response.json()["results"][0]["per_reporter_staleness"]
    last_checkin_time = host_staleness["puptoo"]["last_check_in"]

    # override insights-client.timer to run every 3 min
    override_path = Path("/etc/systemd/system/insights-client.timer.d/override.conf")
    override_content = """
        [Timer]
        OnCalendar=*:0/3
        Persistent=true
        RandomizedDelaySec=5
        """
    try:
        override_path.parent.mkdir()
        override_path.write_text(override_content)

        subprocess.run(["systemctl", "daemon-reload"])

        # Start the timer to ensure it's active
        subprocess.run(["systemctl", "start", "insights-client.timer"])

        logging.info(f"Initial last_check_in time: {last_checkin_time}")
        logging.info("Waiting for systemd timer to trigger upload...")

        def check_upload_completed():
            """Check if the upload completed by comparing last_check_in times"""
            try:
                response = external_inventory.this_system()
                current_checkin_time = response["per_reporter_staleness"]["puptoo"][
                    "last_check_in"
                ]
                logging.debug(f"Current last_check_in time: {current_checkin_time}")
                return current_checkin_time > last_checkin_time
            except Exception as e:
                logging.debug(f"Error checking upload status: {e}")
                return False

        # Wait for upload to complete via timer (poll every 30s, timeout 10min)
        upload_completed = conftest.loop_until(
            check_upload_completed, poll_sec=30, timeout_sec=10 * 60
        )

        # remove the override.conf for insights-client.timer to avoid multiple uploads
        subprocess.run(["systemctl", "revert", "insights-client.timer"])

        assert upload_completed, (
            "Timer-triggered upload did not complete within 10 minutes. "
            "Check systemd timer status and insights-client logs."
        )

        # Verify the final state
        response = external_inventory.this_system()
        latest_checkin_time = response["per_reporter_staleness"]["puptoo"][
            "last_check_in"
        ]
        logging.info(f"Final last_check_in time: {latest_checkin_time}")
        assert last_checkin_time < latest_checkin_time

    finally:
        subprocess.run(["systemctl", "revert", "insights-client.timer"])
