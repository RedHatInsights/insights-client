"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import conftest
from constants import REGISTERED_FILE, UNREGISTERED_FILE, MACHINE_ID_FILE
import contextlib
import os
import pytest
from pytest_client_tools.util import Version
from time import sleep

pytestmark = pytest.mark.usefixtures("register_subman")


@pytest.mark.tier1
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
    registration_status = insights_client.run("--status", selinux_context=None)
    if insights_client.config.legacy_upload:
        assert "Insights API confirms registration." in registration_status.stdout
    else:
        assert "This host is registered.\n" == registration_status.stdout


@pytest.mark.tier1
def test_status_registered_only_locally(
    external_candlepin, insights_client, external_inventory
):
    """
    :id: 2ca3be87-8322-47b8-b451-9ea7fa3dbeef
    :title: Test insights-client --status when registered only locally
    :description:
        This test verifies that when the insights client is registered only
        locally, the `insights-client --status` command outputs the correct
        registration status
    :tags: Tier 1
    :steps:
        1. Set the legacy_upload to False
        2. Register the insights-client
        3. Delete the host from the Inventory
        4. Run `insights-client --status` command
    :expectedresults:
        1. The client registers successfully
        2. Wait time completes without issues
        3. The host is deleted from the Inventory
        4. On systems with version 3.5.7 and higher, output is "This host is
            registered.", the registered file exists, the unregistered file
            does not exist, and the machine ID file exists. Otherwise, output
            is "This host is unregistered."
    """
    insights_client.config.legacy_upload = False
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)
    system_id = external_inventory.this_system()["id"]
    external_inventory.delete(path=f"hosts/{system_id}")
    response = external_inventory.get(path=f"hosts?insights_id={insights_client.uuid}")
    assert response.json()["total"] == 0

    registration_status = insights_client.run(
        "--status", check=False, selinux_context=None
    )
    if insights_client.core_version >= Version(3, 5, 7):
        assert "This host is registered.\n" == registration_status.stdout
        assert os.path.exists(REGISTERED_FILE)
        assert not os.path.exists(UNREGISTERED_FILE)
        assert os.path.exists(MACHINE_ID_FILE)
    else:
        assert "This host is unregistered.\n" == registration_status.stdout


@pytest.mark.tier1
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
        2. If 'legacy_upload' is True, return code is 1 and output contains
            "Insights API says this machine is NOT registered."
            If 'legacy_upload' is False, on systems with version 3.5.3 and
            higher, return code is 1 and output contains "This host is
            unregistered.". Otherwise return code is 0 and output contains
            "This host is unregistered.\n"
    """
    # running unregistration to ensure system is unregistered
    with contextlib.suppress(Exception):
        insights_client.unregister()
    assert conftest.loop_until(lambda: not insights_client.is_registered)

    registration_status = insights_client.run(
        "--status", check=False, selinux_context=None
    )
    if insights_client.config.legacy_upload:
        assert registration_status.returncode == 1
        assert (
            "Insights API says this machine is NOT registered."
            in registration_status.stdout
        )
    else:
        if insights_client.core_version >= Version(3, 5, 3):
            assert registration_status.returncode == 1
        else:
            assert registration_status.returncode == 0
        assert "This host is unregistered.\n" == registration_status.stdout
