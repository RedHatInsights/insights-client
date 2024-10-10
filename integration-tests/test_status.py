"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: sst_csi_client_tools
:caseautomation: Automated
:upstream: Yes
"""

import contextlib
import pytest
from time import sleep
import conftest

pytestmark = pytest.mark.usefixtures("register_subman")


def test_status_registered(external_candlepin, insights_client):
    """
    :id: 624b01fc-e841-4c26-afd8-bb28eaf7fe75
    :title: Test insights-client --status when registered
    :description:
        This test verifies that when the insights client is registered, the
        `insights-client --status` command outputs the correct registration status
    :reference:
    :tags: Tier 1
    :steps:
        1. Register the insights-client
        2. Wait briefly to ensure inventory is up-to-date
        3. Run `insights-client --status` command
    :expectedresults:
        1. The client registers successfully
        2. Wait time completes without issues
        3. If 'legacy_upload' is True, output contains "Insights API confirms
            registration." If 'legacy_upload' is False, output is "This host
            is registered.\n"
    """
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)
    # Adding a small wait to ensure inventory is up-to-date
    sleep(5)
    registration_status = insights_client.run("--status")
    if insights_client.config.legacy_upload:
        assert "Insights API confirms registration." in registration_status.stdout
    else:
        assert "This host is registered.\n" == registration_status.stdout


def test_status_unregistered(external_candlepin, insights_client):
    """
    :id: aa37831a-a581-44db-a7c9-de8161767c7e
    :title: Test insights-client --status when unregistered
    :description:
        This test verifies that when the insights client is unregistered, the
        `insights-client --status` command outputs the correct unregistration
        status
    :reference:
    :tags: Tier 1
    :steps:
        1. Unregister the insights client to ensure it's unregistered
        2. Run `insights-client --status` command
    :expectedresults:
        1. The client unregisters successfully
        2. If 'legacy_upload' is True return code is 1 and output contains
            "Insights API says this machine is NOT registered."
            If 'legacy_upload' is False return code is 0 and output contains
            "This host is unregistered.\n"
    """
    # running unregistration to ensure system is unregistered
    with contextlib.suppress(Exception):
        insights_client.unregister()
    assert conftest.loop_until(lambda: not insights_client.is_registered)

    registration_status = insights_client.run("--status", check=False)
    if insights_client.config.legacy_upload:
        assert registration_status.returncode == 1
        assert (
            "Insights API says this machine is NOT registered."
            in registration_status.stdout
        )
    else:
        assert registration_status.returncode == 0
        assert "This host is unregistered.\n" == registration_status.stdout
