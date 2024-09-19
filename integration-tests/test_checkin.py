import contextlib
import json

import pytest
from constants import HOST_DETAILS
import conftest

pytestmark = pytest.mark.usefixtures("register_subman")


def test_ultralight_checkin(insights_client, test_config):
    """test --checkin
    Sends nothing but canonical facts to update the host stale and updated timestamp
    """
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    # Performing check-results operation provides latest host data in host-details.json
    insights_client.run("--check-results")
    with open(HOST_DETAILS, "r") as data_file:
        data = json.load(data_file)
        stale_ts_before_checkin = data["results"][0]["stale_timestamp"]
        updated_ts_before_checkin = data["results"][0]["updated"]

    # Performing an ultra light check-in
    insights_client.run("--checkin")
    insights_client.run("--check-results")

    with open(HOST_DETAILS, "r") as data_file:
        data = json.load(data_file)
        stale_ts_after_checkin = data["results"][0]["stale_timestamp"]
        updated_ts_after_checkin = data["results"][0]["updated"]

    assert stale_ts_after_checkin > stale_ts_before_checkin
    assert updated_ts_after_checkin > updated_ts_before_checkin


def test_client_checkin_unregistered(insights_client):
    """Call insights client check-in with unregistered client."""
    with contextlib.suppress(Exception):
        insights_client.unregister()
    assert conftest.loop_until(lambda: not insights_client.is_registered)

    checkin_result = insights_client.run("--checkin", check=False)
    assert checkin_result.returncode == 1
    assert (
        "Error: failed to find host with matching machine-id" in checkin_result.stdout
    )
