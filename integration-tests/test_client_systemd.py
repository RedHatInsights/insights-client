import json
import conftest
from constants import HOST_DETAILS
import time
import pytest
import subprocess
from datetime import datetime, timedelta

pytestmark = pytest.mark.usefixtures("register_subman")


def test_data_upload_systemd_timer(insights_client):
    """
    This test aims to verify that insight-client uploads data via systemd timer
    steps:
        1- Register the system
        2- Note the last upload time from host-details
        3- Modify system date time by 24 hours(uploads happens every 24 hours)
        4- Wait for 2 minutes for upload to finish
        5- Refresh host details using --check-results
        6- Verify the host details again to validate last upload time> old one

    """
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    insights_client.run("--check-results")
    host_data = read_host_data()

    last_checkin_time = host_data["per_reporter_staleness"]["puptoo"]["last_check_in"]

    current_datetime = datetime.now()
    new_datetime = current_datetime + timedelta(hours=24)

    formatted_datetime = new_datetime.strftime("%Y-%m-%d %H:%M:%S")
    subprocess.run(["date", "-s", formatted_datetime])

    # wait for upload to finish
    time.sleep(180)

    insights_client.run("--check-results")
    host_data = read_host_data()
    latest_checkin_time = host_data["per_reporter_staleness"]["puptoo"]["last_check_in"]

    assert last_checkin_time < latest_checkin_time


def read_host_data():
    with open(HOST_DETAILS, "r") as data_file:
        file_content = json.load(data_file)
        host_data = file_content["results"][0]
    return host_data
