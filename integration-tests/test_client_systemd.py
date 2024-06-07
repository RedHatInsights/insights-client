import os

import conftest
from time import sleep
import pytest
import subprocess

pytestmark = pytest.mark.usefixtures("register_subman")


def test_data_upload_systemd_timer(insights_client, external_inventory):
    """
    This test aims to verify that insight-client uploads data via systemd timer
    steps:
        1- Register the system
        2- Note the last_check_in in host details from inventory
        3- Edit insights-client timer to run every 3 minutes (24 hours is
        too long to wait for a test, 3 min appears be a decent wait)
        4- Wait for upload to finish
        5- Again note the last_check_in in host details from inventory
        6- Validate step 5 last_check_in > step 2 last_check_in

    """

    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    machine_id = insights_client.uuid
    # fetching host details to note last_check_in time
    response = external_inventory.get(path=f"hosts?insights_id={machine_id}")
    last_checkin_time = response.json()["results"][0]["per_reporter_staleness"][
        "puptoo"
    ]["last_check_in"]

    # override insights-client.timer to run every 3 min
    override_path = "/etc/systemd/system/insights-client.timer.d/override.conf"
    override_content = """
        [Timer]
        OnCalendar=*:0/3
        Persistent=true
        RandomizedDelaySec=5
        """
    os.makedirs(os.path.dirname(override_path), exist_ok=True)
    with open(override_path, "w") as override_file:
        override_file.write(override_content)

    subprocess.run(["systemctl", "daemon-reload"])
    # subprocess.run(['systemctl', 'restart', 'insights-client.timer'])

    sleep(300)  # sleep for the period when timer is triggered and upload happens

    # remove the override.conf for insights-client.timer to avoid multiple uploads
    subprocess.run(["systemctl", "revert", "insights-client.timer"])

    # fetch the last_check_in time
    machine_id = insights_client.uuid
    response = external_inventory.get(path=f"hosts?insights_id={machine_id}")
    latest_checkin_time = response.json()["results"][0]["per_reporter_staleness"][
        "puptoo"
    ]["last_check_in"]

    assert last_checkin_time < latest_checkin_time
