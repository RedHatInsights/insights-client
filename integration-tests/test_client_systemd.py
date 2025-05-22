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
from time import sleep
import pytest
import subprocess
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
    :reference:
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

        sleep(60 * 5)  # sleep for the period when timer is triggered and upload happens

        # remove the override.conf for insights-client.timer to avoid multiple uploads
        subprocess.run(["systemctl", "revert", "insights-client.timer"])

        # fetch the last_check_in time
        response = external_inventory.this_system()
        latest_checkin_time = response["per_reporter_staleness"]["puptoo"][
            "last_check_in"
        ]
        assert last_checkin_time < latest_checkin_time

    finally:
        subprocess.run(["systemctl", "revert", "insights-client.timer"])
