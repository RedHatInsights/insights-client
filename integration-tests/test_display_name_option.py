import pytest
import uuid
import logging
from conftest import loop_until

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.usefixtures("register_subman")

unique_hostname = f"test-qa.{uuid.uuid4()}.csi-client-tools.example.com"

def test_register_with_display_name(insights_client, fetch_from_inventory):
    """Test insights-client --register --display-name SOME_NEW_HOSTNAME

    The current display name should appear in inventory
    """
    status = insights_client.run("--register","--display-name",unique_hostname)
    assert loop_until(lambda : insights_client.is_registered)
    assert (
        "Successfully registered host" in status.stdout
    ), f"An application should inform about successfull registration"

    assert (
        f"as {unique_hostname}"  in status.stdout
    ), f"An application should inform that a system is registered with the given hostname"
    response = fetch_from_inventory()
    logger.debug(f"response from console {response}")
    
    record = response.results[0]
    assert 'display_name' in record.keys()
    assert unique_hostname == record['display_name']

