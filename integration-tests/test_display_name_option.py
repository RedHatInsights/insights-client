import string

import pytest
import uuid
import logging
import json
import random
import conftest

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


def test_display_name(insights_client):
    """Test insights-client --display-name"""
    new_hostname = generate_unique_hostname()
    insights_client.run("--register")
    assert conftest.loop_until(lambda: insights_client.is_registered)

    response = insights_client.run("--display-name", new_hostname)
    logger.debug(f"response from console {response}")

    assert f"Display name updated to {new_hostname}" in response.stdout

    def display_name_changed():
        insights_client.run("--check-results")
        host_details = read_host_details()
        logger.debug(f"host details {host_details}")
        record = host_details["results"][0]
        return new_hostname == record["display_name"]

    assert conftest.loop_until(display_name_changed)


def test_register_with_display_name(insights_client):
    """Test insights-client --register --display-name SOME_NEW_HOSTNAME

    The current display name should appear in inventory
    """
    unique_hostname = generate_unique_hostname()

    status = insights_client.run("--register", "--display-name", unique_hostname)
    assert conftest.loop_until(lambda: insights_client.is_registered)
    assert unique_hostname in status.stdout
    insights_client.run("--check-results")
    host_details = read_host_details()
    logger.debug(f"content of host-details.json {host_details}")

    record = host_details["results"][0]
    assert "display_name" in record.keys()
    assert unique_hostname == record["display_name"]


def test_register_twice_with_different_display_name(
    insights_client, test_config, subtests
):
    """Try to register a host but with different display-name than set before

    Set new display_name and try to register twice.

    Registering twice, even with a different display_name set, will do nothing.
    The `register` method does check if the host changed at all,
    it only checks the machine_id
    """
    insights_id = None
    unique_hostname = generate_unique_hostname()
    unique_hostname_02 = generate_unique_hostname()

    with subtests.test(msg="the first registration"):
        status = insights_client.run("--register", "--display-name", unique_hostname)
        assert unique_hostname in status.stdout

        assert conftest.loop_until(lambda: insights_client.is_registered)
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

        assert conftest.loop_until(lambda: insights_client.is_registered)
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
def test_invalid_display_name(invalid_display_name, insights_client):
    """Tries to set an invalid display name.
    invalid display names:

    - bigger than 200 characters
    - empty string
    """
    insights_client.run("--register")
    assert conftest.loop_until(lambda: insights_client.is_registered)

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


def test_display_name_disable_autoconfig_and_autoupdate(insights_client, test_config):
    """
    Ref : https://issues.redhat.com/browse/ESSNTL-2230

    Steps:
    1. Register rhel system for subscriptions.
    2. In the insights-client.conf:
    Set auto_config=False auto_update=False, and set display_name.

        Note:
        1) When auto_config=false, need to also configure:

        auto_config=False
        base_url=satellite_IP:443/redhat_access/r/insights
        cert_verify=True
        authmethod=CERT

        Refer: https://issues.redhat.com/browse/RHEL-19435

        2) This case works with legacy_upload=False on prod and stage envs,
        and works with both legacy_upload=False and legacy_upload=True
        on Satellite env.

    3. Register insights.
    4. Check the results:
        1) Registration insights with display name is successful.
        2) Host visible in the c.r.c.
    """
    # configuration on insights-client.conf
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
    status = insights_client.run("--register")
    assert conftest.loop_until(lambda: insights_client.is_registered)
    assert unique_hostname in status.stdout

    # check the display name on CRC
    insights_client.run("--check-results")
    host_details = read_host_details()
    logger.debug(f"content of host-details.json {host_details}")
    record = host_details["results"][0]
    assert unique_hostname == record["display_name"]
