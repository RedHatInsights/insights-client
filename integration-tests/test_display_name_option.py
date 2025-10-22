"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import string
import pytest
import uuid
import logging
import json
import random
import subprocess
from pytest_client_tools.util import loop_until

from constants import HOST_DETAILS

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.usefixtures("register_subman")


def read_host_details():
    with open(HOST_DETAILS, "r") as data_file:
        return json.load(data_file)


def generate_unique_hostname():
    return f"test-qa.{uuid.uuid4()}.csi-client-tools.example.com"


def create_random_string(n: int):
    return "".join(random.choices(string.ascii_letters, k=n))


@pytest.mark.tier1
def test_display_name(insights_client, test_config):
    """
    :id: 4758cb21-03b4-4334-852c-791b7c82b50a
    :title: Test updating display name via '--display-name'
    :description:
        This test verifies that a registered host's display name can be
        updated using the --display-name option.
    :tags: Tier 1
    :steps:
        1. Generate a unique hostname and register the insights-client
        2. Update the display name using --display-name <NEW_HOSTNAME>
        3. Verify the display name has been updated in the host details
    :expectedresults:
        1. A unique hostname is generated and insights-client is registered
        2. The command outputs 'Display name updated to <NEW_HOSTNAME>'
        3. The display_name in host detailes matches the new hostname
    """
    if "satellite" in test_config.environment:
        pytest.skip(reason="Test is not applicable to Satellite")
    new_hostname = generate_unique_hostname()
    insights_client.run("--register")
    assert loop_until(lambda: insights_client.is_registered)

    response = insights_client.run("--display-name", new_hostname)
    logger.debug(f"response from console {response}")

    assert f"Display name updated to {new_hostname}" in response.stdout

    def display_name_changed():
        insights_client.run("--check-results")
        host_details = read_host_details()
        logger.debug(f"host details {host_details}")
        record = host_details["results"][0]
        return new_hostname == record["display_name"]

    assert loop_until(display_name_changed)


@pytest.mark.tier1
def test_register_with_display_name(insights_client):
    """
    :id: d127b2bf-2f6d-4b02-bb8e-99036bfc4291
    :title: Test registration with custom display name
    :description:
        This test ensures that registering the insights-client with a custom
        display name sets the display name correctly in host details
    :tags: Tier 1
    :steps:
        1. Generate a unique hostname
        2. Register the insights-client using '--register --display-name'
        3. Verify the display_name in host details
    :expectedresults:
        1. Unique hostname is generated
        2. The client registers and successfully outputs the unique hostname
        3. The display_name in host details matches the unique hostname
    """
    unique_hostname = generate_unique_hostname()

    status = insights_client.run("--register", "--display-name", unique_hostname)
    assert loop_until(lambda: insights_client.is_registered)
    assert unique_hostname in status.stdout
    insights_client.run("--check-results")
    host_details = read_host_details()
    logger.debug(f"content of host-details.json {host_details}")

    record = host_details["results"][0]
    assert "display_name" in record.keys()
    assert unique_hostname == record["display_name"]


@pytest.mark.tier1
def test_register_twice_with_different_display_name(
    insights_client, test_config, subtests
):
    """
    :id: 3d28562d-16c4-4fb1-b9b1-f39044e05ef5
    :title: Test re-registration with different display names
    :description:
        This test checks that registering the insights-client twice with different
        display names does not change the insights_id and display_name is updated
    :tags: Tier 1
    :steps:
        1. Generate a unique hostname
        2. Register the insights-client using '--register --display-name'
        3. Record the machine ID and display_name
        4. Generate another unique hostname
        5. Register the insights-client using '--register --display_name'
        6. Compare the old display_name and insights_id with those updated
    :expectedresults:
        1. Unique hostname is generated
        2. The client registers and successfully outputs the unique hostname
        3. Information are successfully retrieved and stored
        4. Unique hostname is generated
        5. The output indicates that the host is already registered but updates the
            display_name to the new one
        6. Insights_id stayed unchanged while display_name changed to the latest one
    """
    insights_id = None
    unique_hostname = generate_unique_hostname()
    unique_hostname_02 = generate_unique_hostname()

    with subtests.test(msg="the first registration"):
        status = insights_client.run("--register", "--display-name", unique_hostname)
        assert unique_hostname in status.stdout

        assert loop_until(lambda: insights_client.is_registered)
        insights_client.run("--check-results")
        host_details = read_host_details()
        record = host_details["results"][0]
        assert "display_name" in record.keys()
        assert unique_hostname == record["display_name"]
        insights_id = record["insights_id"]

    (status, host_details, record) = (None, None, None)
    with subtests.test(msg="The second registration"):
        status = insights_client.run("--register", "--display-name", unique_hostname_02)
        registration_message = "This host has already been registered"
        assert registration_message in status.stdout

        assert loop_until(lambda: insights_client.is_registered)
        insights_client.run("--check-results")
        host_details = read_host_details()
        logger.debug(f"content of host-details.json: {host_details}")
        record = host_details["results"][0]
        assert "display_name" in record.keys()
        assert unique_hostname_02 == record["display_name"]
        assert (
            insights_id == record["insights_id"]
        ), "machine-id should remain the same even display-name has been changed"


@pytest.mark.parametrize("invalid_display_name", [create_random_string(201), ""])
@pytest.mark.tier1
def test_invalid_display_name(invalid_display_name, insights_client):
    """
    :id: 9cbdd1a6-9ee3-4799-baaf-15c3894ca55b
    :title: Test handling of invalid display names
    :parametrized: yes
    :description:
        This test verifies that attempting to set an invalid display_name is rejected
        and does not alter the current display_name value
    :tags: Tier 1
    :steps:
        1. Register the insights-client
        2. Record the original display_name value
        3. Attempt to update the display_name using an invalid value
        4. Verify that display_name stayed unchanged
    :expectedresults:
        1. Insights-client is registered
        2. Original display_name value is saved
        3. The command fails with an error code 1 and a message
            'Could not update display name'
        4. The display_name in host details matches the saved original
    """
    insights_client.run("--register")
    assert loop_until(lambda: insights_client.is_registered)

    insights_client.run("--check-results")
    host_details = read_host_details()
    origin_display_name = host_details["results"][0]["display_name"]

    response = insights_client.run("--display-name", invalid_display_name, check=False)
    assert response.returncode == 1
    assert "Could not update display name" in response.stdout

    insights_client.run("--check-results")
    host_details = read_host_details()
    logger.debug(f"content of host-details.json {host_details}")

    record = host_details["results"][0]
    assert (
        origin_display_name == record["display_name"]
    ), "display-name should remain unchanged when new display-name is rejected"


@pytest.mark.tier2
def test_display_name_disable_autoconfig_and_autoupdate(insights_client, test_config):
    """
    :id: 8cdbc0ff-42ba-41e8-bd3f-31550ccac081
    :title: Test registration with display_name when auto-config and auto-update
        are disabled
    :description:
        This test verifies that the insights-client can be registered with a
        display_name name even when auto_config and auto_update are set to
        False and host appears on cloud with the correct display name
    :reference: https://issues.redhat.com/browse/RHEL-19435
    :tags: Tier 2
    :steps:
        1. Configure insights-client.conf with auto_config and auto_update set to False
            and display_name set
        2. Register the insights-client
        3. Verify the host is visible in cloud.redhat.com with the correct display_name
            set in the configuration file
    :expectedresults:
        1. Configuration is set and successfully saved
        2. Insights-client is registered
        3. Host appears in inventory with the display name matching the one that was set
    """
    # configuration on insights-client.conf
    insights_client.config.legacy_upload = False
    insights_client.config.cert_verify = True
    insights_client.config.auto_update = False
    insights_client.config.auto_config = False
    insights_client.config.authmethod = "CERT"
    unique_hostname = generate_unique_hostname()
    insights_client.config.display_name = unique_hostname
    if "satellite" in test_config.environment:
        satellite_hostname = test_config.get("candlepin", "host")
        satellite_port = test_config.get("candlepin", "port")
        insights_client.config.base_url = (
            satellite_hostname + ":" + str(satellite_port) + "/redhat_access/r/insights"
        )
        insights_client.config.cert_verify = "/etc/rhsm/ca/katello-server-ca.pem"
    elif "prod" in test_config.environment:
        insights_client.config.base_url = "cert.cloud.redhat.com/api"
    elif "stage" in test_config.environment:
        insights_client.config.base_url = "cert.cloud.stage.redhat.com/api"
    insights_client.config.save()

    # register insights
    try:
        status = insights_client.run("--register")
    except subprocess.CalledProcessError as e:
        if (
            "certificate verify failed" in e.stdout.lower()
            or "certificate verify failed" in str(e)
        ):
            pytest.skip("Skipping test due to SSL certificate verification failure")
        raise
    assert loop_until(lambda: insights_client.is_registered)
    assert unique_hostname in status.stdout

    # check the display name on CRC
    insights_client.run("--check-results")
    host_details = read_host_details()
    logger.debug(f"content of host-details.json {host_details}")
    record = host_details["results"][0]
    assert unique_hostname == record["display_name"]
