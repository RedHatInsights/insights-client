import pytest
import conftest
from pytest_client_tools.util import Version

pytestmark = pytest.mark.usefixtures("register_subman")


def test_insights_client_version_in_inventory(insights_client, external_inventory):
    """
    Verify running insights-client creates a new host on Inventory and the host has
    the insights client and egg version information available

        test_steps:
            1. Register the system to Insights
            4. Retrieve the system profile from Inventory
        expected_results:
            1. Successful registration to insights server
            2. The system profile is successfully retrieved from Inventory
            3. system data retrieved from Inventory has client and egg version info
    """
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    system_profile = external_inventory.this_system_profile()

    assert insights_client.version == Version(system_profile["insights_client_version"])
    assert insights_client.core_version == Version(
        (system_profile["insights_egg_version"].split("-"))[0]
    )
