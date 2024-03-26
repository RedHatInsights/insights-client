import pytest
import uuid
import logging
from conftest import loop_until

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.usefixtures("register_subman")


def test_register_with_display_name(insights_client, fetch_from_inventory):
    """Test insights-client --register --display-name SOME_NEW_HOSTNAME

    The current display name should appear in inventory
    """
    unique_hostname = f"test-qa.{uuid.uuid4()}.csi-client-tools.example.com"

    status = insights_client.run("--register", "--display-name", unique_hostname)
    assert loop_until(lambda: insights_client.is_registered)
    assert (
        "Successfully registered host" in status.stdout
    ), f"An application should inform about successfull registration"

    assert (
        f"as {unique_hostname}" in status.stdout
    ), f"An application should inform that a system is registered with the given hostname"
    response = fetch_from_inventory()
    logger.debug(f"response from console {response}")

    record = response["results"][0]
    assert "display_name" in record.keys()
    assert unique_hostname == record["display_name"]


def test_register_twice_with_different_display_name(
    insights_client, test_config, fetch_from_inventory, subtests
):
    """Try to register a host but with different display-name than set before

    Set new display_name and try to register twice.

    Registering twice, even with a different display_name set, will do nothing.
    The `register` method does check if the host changed at all, it only checks the machine_id

    """
    insights_id = None
    unique_hostname = f"test-qa.{uuid.uuid4()}.csi-client-tools.example.com"
    unique_hostname_02 = f"test-qa.{uuid.uuid4()}.csi-client-tools.example.com"

    with subtests.test(msg="the first registration"):
        status = insights_client.run("--register", "--display-name", unique_hostname)
        assert "Successfully registered host" in status.stdout
        assert f"as {unique_hostname}" in status.stdout

        assert loop_until(lambda: insights_client.is_registered)
        response = fetch_from_inventory()
        record = response["results"][0]
        assert "display_name" in record.keys()
        assert unique_hostname == record["display_name"]
        insights_id = record["insights_id"]

    (status, response, record) = (None, None, None)
    with subtests.test(msg="The second registration"):
        status = insights_client.run("--register", "--display-name", unique_hostname_02)
        registration_message = ('stage' in test_config.environment) \
            and "This machine has already been registered" \
            or "This host has already been registered"
        assert registration_message in status.stdout

        assert loop_until(lambda: insights_client.is_registered)
        response = fetch_from_inventory()
        logger.debug(f"response from inventory: {response}")
        record = response["results"][0]
        assert "display_name" in record.keys()
        assert unique_hostname_02 == record["display_name"]
        assert (
            insights_id == record["insights_id"]
        ), "machine-id should remain the same even display-name has been changed"
