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
from constants import REGISTERED_FILE, UNREGISTERED_FILE, MACHINE_ID_FILE
import contextlib
import os
import pytest
from pytest_client_tools.util import Version
import logging

pytestmark = pytest.mark.usefixtures("register_subman")


@pytest.mark.tier1
def test_status_registered(external_candlepin, insights_client):
    """
    :id: 624b01fc-e841-4c26-afd8-bb28eaf7fe75
    :title: Test insights-client --status when registered
    :description:
        This test verifies that when the insights client is registered, the
        `insights-client --status` command outputs the correct registration status
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
            is registered."
    """
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    logging.info("Waiting for registration status to be properly reflected...")

    def check_status_command():
        """Check if --status command returns the expected registration message"""
        try:
            registration_status = insights_client.run("--status")
            if insights_client.config.legacy_upload:
                expected_msg = "Insights API confirms registration."
                status_correct = expected_msg in registration_status.stdout
                if status_correct:
                    logging.info("Legacy upload status confirmed")
                else:
                    logging.debug(
                        f"Status not yet correct. Current output: "
                        f"{registration_status.stdout}"
                    )
            else:
                expected_msg = "This host is registered.\n"
                status_correct = registration_status.stdout == expected_msg
                if status_correct:
                    logging.info("Registration status confirmed")
                else:
                    logging.debug(
                        f"Status not yet correct. Expected: {repr(expected_msg)}, "
                        f"Got: {repr(registration_status.stdout)}"
                    )
            return status_correct
        except Exception as e:
            logging.debug(f"Error checking status command: {e}")
            return False

    # Wait for status to be correct (poll every 5 seconds, timeout after 2 minutes)
    status_ready = conftest.loop_until(
        check_status_command, poll_sec=5, timeout_sec=2 * 60
    )

    assert status_ready, (
        "Registration status did not become available within 2 minutes. "
        "Check insights-client registration and backend synchronization."
    )


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
    machine_id = insights_client.uuid
    external_inventory.delete(path=f"hosts/{external_inventory.this_system()['id']}")
    response = external_inventory.get(path=f"hosts?insights_id={machine_id}")
    assert response.json()["total"] == 0

    registration_status = insights_client.run("--status", check=False)
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
            "This host is unregistered."
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
        if insights_client.core_version >= Version(3, 5, 3):
            assert registration_status.returncode == 1
        else:
            assert registration_status.returncode == 0
        assert "This host is unregistered.\n" == registration_status.stdout
