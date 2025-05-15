"""
:casecomponent: insights-client
:requirement: RHSS-291297
:polarion-project-id: RHELSS
:polarion-include-skipped: false
:polarion-lookup-method: id
:subsystemteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import conftest
import pytest
import distro

pytestmark = [
    pytest.mark.usefixtures("register_subman"),
    pytest.mark.skipif(
        distro.id() != "rhel",
        reason="Skipping tests because OS ID is not RHEL",
        allow_module_level=True,
    ),
]


@pytest.mark.tier1
def test_compliance_option(insights_client):
    """
    :id: caa8b3e1-9347-494c-a1f5-1fa670136834
    :title: Test compliance option
    :reference: https://issues.redhat.com/browse/CCT-1229
    :description:
        This test verifies that running the --compliance will not result in a failure
    :tags: Tier 1
    :steps:
        1. Run insights-client with --compliance option
        2. Register insights-client
        3. Run insights-client with --compliance option
    :expectedresults:
        1. Command will fail with instructions for user to register
        2. System is successfully registered
        3. The output of the command either informs user that system is not associated
            with any policies or the report will be successfully uploaded
    """
    compliance_before_registration = insights_client.run("--compliance", check=False)
    assert compliance_before_registration.returncode == 1
    assert (
        "This host has not been registered. Use --register to register this host"
        in compliance_before_registration.stdout
    )

    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    compliance_after_registration = insights_client.run("--compliance", check=False)
    if compliance_after_registration.returncode == 1:
        assert (
            "System is not associated with any policies."
            in compliance_after_registration.stdout
        )
    else:
        assert "Successfully uploaded report" in compliance_after_registration.stdout


@pytest.mark.tier1
def test_compliance_policies_option(insights_client):
    """
    :id: ad3a2073-3a2e-485e-bc7b-fede2111a06a
    :title: Test compliance-policies option
    :reference: https://issues.redhat.com/browse/CCT-1229
    :description:
        This test verifies that running the --compliance-policies
        will not result in a failure
    :tags: Tier 1
    :steps:
        1. Register insights-client
        2. Run insights-client with --compliance-policies option
    :expectedresults:
        1. System is successfully registered
        2. The output of the command either informs the user that system is not
            assignable to any policy or ID of available policy is found and
            displayed
    """
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    compliance_policies = insights_client.run("--compliance-policies", check=False)
    if compliance_policies.returncode == 1:
        assert "System is not assignable to any policy." in compliance_policies.stdout
        assert (
            "Create supported policy using the Compliance web UI."
            in compliance_policies.stdout
        )
    else:
        assert "ID" in compliance_policies.stdout
