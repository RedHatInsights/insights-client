"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import pytest
from pytest_client_tools.util import Version, loop_until

pytestmark = pytest.mark.usefixtures("register_subman")


@pytest.mark.tier1
def test_unregister(insights_client):
    """
    :id: ecaeeddc-4c8b-4f17-8d69-1c81d2c7c744
    :title: Test unregister
    :description:
        This test verifies that the insights-client can be unregistered
        successfully after being registered.
    :tags: Tier 1
    :steps:
        1. Register the insights-client if not registered
        2. Run `insights-client --unregister` command
        3. Confirm the client is unregistered
    :expectedresults:
        1. The client registers successfully
        2. On systems with Insights Core version >= 3.5.11, the command outputs
            "Successfully unregistered this host." Otherwise, the command
            outputs "Successfully unregistered from the Red Hat Insights Service"
        3. Client unregistration is confirmed
    """
    insights_client.register()
    assert loop_until(lambda: insights_client.is_registered)

    unregistration_status = insights_client.run("--unregister")
    if insights_client.core_version >= Version(3, 5, 11):
        assert "Successfully unregistered this host." in unregistration_status.stdout
    else:
        assert (
            "Successfully unregistered from the Red Hat Insights Service"
            in unregistration_status.stdout
        )
    assert loop_until(lambda: not insights_client.is_registered)


@pytest.mark.tier1
def test_unregister_twice(insights_client):
    """
    :id: bfff1b33-5f19-42d2-a6ff-4598975873e5
    :title: Test unregister already unregistered system
    :description:
        This test verifies that attempting to unregister the insights client
        when it is already unregistered behaves as expected. It checks that
        the first unregistration succeeds and that subsequent unregistration
        attempts produce the appropriate error message and return code
    :tags: Tier 1
    :steps:
        1. Register the insights-client
        2. Unregister the client for the first time
        3. Attempt to unregister the client a second time
    :expectedresults:
        1. The client registers successfully
        2. On systems with Insights Core version >= 3.5.11, the command outputs
            "Successfully unregistered this host." Otherwise, the command
            outputs "Successfully unregistered from the Red Hat Insights Service"
        3. Command returns exit code 1 and outputs "This host is not registered,
            unregistration is not applicable."
    """
    insights_client.register()
    assert loop_until(lambda: insights_client.is_registered)

    # unregister once
    unregistration_status = insights_client.run("--unregister")
    assert loop_until(lambda: not insights_client.is_registered)
    if insights_client.core_version >= Version(3, 5, 11):
        assert "Successfully unregistered this host." in unregistration_status.stdout
    else:
        assert (
            "Successfully unregistered from the Red Hat Insights Service"
            in unregistration_status.stdout
        )

    # unregister twice
    unregistration_status = insights_client.run("--unregister", check=False)
    assert loop_until(lambda: not insights_client.is_registered)
    assert unregistration_status.returncode == 1
    assert (
        "This host is not registered, unregistration is not applicable."
        in unregistration_status.stdout
    )
