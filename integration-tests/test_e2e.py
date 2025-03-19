"""
:casecomponent: insights-client
:requirement: RHSS-291297
:polarion-project-id: RHELSS
:polarion-include-skipped: false
:polarion-lookup-method: id
:subsystemteam: sst_csi_client_tools
:caseautomation: Automated
:upstream: Yes
"""

import pytest
import conftest
from pytest_client_tools.util import Version

pytestmark = pytest.mark.usefixtures("register_subman")


def test_insights_client_version_in_inventory(insights_client, external_inventory):
    """
    :id: 1d5d101e-94ad-4404-900f-f86a26450c3f
    :title: Verify insights-client version in Inventory
    :description:
        Ensure that running insights-client creates a new host entry in the
        Inventory and includes both the insights-client and egg version information
    :reference:
    :tags: Tier 1
    :steps:
        1. Register the system with insights-client
        2. Confirm registration status
        3. Retrieve the system profile from the Inventory
    :expectedresults:
        1. Insights-client is registered
        2. The system profile is retrieved from the Inventory
        3. The system profile includes insights-client and egg version information
    """
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    system_profile = external_inventory.this_system_profile()

    assert insights_client.version == Version(system_profile["insights_client_version"])
    assert insights_client.core_version == Version(
        (system_profile["insights_egg_version"].split("-"))[0]
    )
