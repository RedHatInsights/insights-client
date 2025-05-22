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

import contextlib
import json
import pytest
from pytest_client_tools.util import Version

from constants import HOST_DETAILS
import conftest

pytestmark = pytest.mark.usefixtures("register_subman")


@pytest.mark.tier2
def test_ultralight_checkin(insights_client, test_config):
    """
    :id: c662fd5e-0751-45e4-8477-6b0d27f735ac
    :title: Test lightweight check-in updates staleness timestamps
    :description:
        This test verifies that performing an ultra-light check-in with the
        insights-client updates the host's 'stale_timestamps' and 'updated'
        fields on the server
    :reference:
    :tags: Tier 2
    :steps:
        1. Register the insights-client
        2. Run '--check-results' and record the 'stale_timestamp' and 'updated'
            timestamps before check-in
        3. Perform an ultra-light check-in ny running '--checkin'
        4. Run '--check-results' and record the 'stale_timestamp' and 'updated'
            timestamps again
        5. Verify that timestamps were updated successfully
    :expectedresults:
        1. Insights-client is registered
        2. The initial timestamps were retrieved and recorded
        3. The check-in completes without any errors
        4. The updated timestamps were retrieved and recorded
        5. Both updated timestamps will be greater than before check-in
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


@pytest.mark.tier1
def test_client_checkin_unregistered(insights_client):
    """
    :id: 91331995-20c2-4d44-8abe-74a3e7d28309
    :title: Test check-in fails for unregistered client
    :description:
        This test verifies that attempting to perform check-in while unregistered
        fails with appropriate error message
    :reference:
    :tags: Tier 1
    :steps:
        1. Unregister the insights-client if registered
        2. Attempt to perform a check-in by running '--checkin'
    :expectedresults:
        1. Insights-client is unregistered successfully
        2. The check-in fails with return code 1 and message 'Error: failed
            to find host with matching machine-id'
    """
    with contextlib.suppress(Exception):
        insights_client.unregister()
    assert conftest.loop_until(lambda: not insights_client.is_registered)

    checkin_result = insights_client.run("--checkin", check=False)
    if insights_client.core_version >= Version(3, 4, 25):
        assert checkin_result.returncode > 0
        assert "This host is not registered" in checkin_result.stdout
    else:
        assert checkin_result.returncode == 1
        assert (
            "Error: failed to find host with matching machine-id"
            in checkin_result.stdout
        )
