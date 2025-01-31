"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: sst_csi_client_tools
:caseautomation: Automated
:upstream: Yes
"""


def test_version(insights_client):
    """
    :id: 7ec671cb-39ae-4cda-b279-f05d7c835d5d
    :title: Test --version outputs client and core versions
    :description:
        This test verifies that running `insights-client --version` outputs
        both the client and core version information
    :tags: Tier 1
    :steps:
        1. Run `insights-client --version`
        2. Check the output for "Client: " and "Core: "
    :expectedresults:
        1. Command executes without errors
        2. Both "Client: " and "Core: " are present in the output
    """
    proc = insights_client.run("--version")
    assert "Client: " in proc.stdout
    assert "Core: " in proc.stdout
