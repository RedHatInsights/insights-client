"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: sst_csi_client_tools
:caseautomation: Automated
:upstream: Yes
"""

import pytest

# the tests need a valid connection to insights so therefore the subman registration
pytestmark = pytest.mark.usefixtures("register_subman")


def test_connection(insights_client):
    """
    :id: ff674d37-0ccc-481c-9f04-91237b8c50d0
    :title: Test connection
    :description:
        This test verifies that the --test-connection option works
        properly, confirming successful connection
    :tier: Tier 1
    :steps:
        1. Run insights-client with --test-connection option
        2. Verify that the connection to the upload URl is successful
        3. Verify that the connection to the API URL is successful
    :expectedresults:
        1. The command executes successfully
        2. The output contains the expected output about upload connection
        3. The output contains expected message about API URL connection
    """
    url_test = "End Upload URL Connection Test: SUCCESS"
    api_test = "End API URL Connection Test: SUCCESS"

    test_connection = insights_client.run("--test-connection")
    assert url_test in test_connection.stdout
    assert api_test in test_connection.stdout


def test_http_timeout(insights_client):
    """
    :id: 46c5fe2a-1553-4f2e-802d-fa10080c72df
    :title: Test HTTP timeout configuration
    :description:
        Verifies that setting a very low http_timeout value causes
        the connection to time out
    :tier: Tier 1
    :steps:
        1. Set the http_timeout option to a very low value and save
        2. Run insights-client with the --test-conection option
        3. Verify that the command fails due to the low timeout setting
        4. Check that the timeout value is in the output
    :expectedresults:
        1. The http_timeout configuration is set and saved
        2. The insights-client command is run
        3. The command fails with a return code of 1
        4. The output mentions timeout value
    """
    insights_client.config.http_timeout = 0.01
    insights_client.config.save()

    output = insights_client.run("--test-connection", check=False)
    assert output.returncode == 1
    assert "timeout=0.01" in output.stdout


def test_noauth_proxy_connection(insights_client, test_config):
    """
    :id: a4bcb7e6-c04f-49d2-8362-525124dc61d9
    :title: Test no-auth proxy connection
    :description:
        Verifies that the insights-client can successfully connect
        through a no-auth proxy when using the --test-connection option
    :tier: Tier 1
    :steps:
        1. Configure insights-client to use no-auth proxy and save
        2. Run insights-client with the --test-connection option
        3. Verify the connection to the upload URL is successful
        4. Verify that the connection to the API URL is successful
    :expectedresults:
        1. Insights-client is configured to use no-auth proxy
        2. The command is executed successfully
        3. The output mentions that the upload URL connection was suuccessful
        4. The output mentions that the API URL connection test was successful
    """
    url_test = "End Upload URL Connection Test: SUCCESS"
    api_test = "End API URL Connection Test: SUCCESS"

    no_auth_proxy: str = (
        "http://"
        + test_config.get("noauth_proxy", "host")
        + ":"
        + str(test_config.get("noauth_proxy", "port"))
    )
    insights_client.config.proxy = no_auth_proxy
    insights_client.config.save()

    test_connection = insights_client.run("--test-connection")
    assert url_test in test_connection.stdout
    assert api_test in test_connection.stdout


def test_auth_proxy_connection(insights_client, test_config):
    """
    :id: 0b3e91d6-3b8b-42c7-8f3b-f7ee1728c311
    :title: Test auth-proxy connection
    :description:
        Verifies that the insights-client can successfully connect
        through an authenticated proxy
    :tier: Tier 1
    :steps:
        1. Configure insights-client to use auth proxy and save
        2. Run the insights-client with --test-connection option
        3. Verify the connection to the upload URL is successful
        4. Verify that the connection to the API URL is successful
    :expectedresults:
        1. Insights-client is configured to use auth proxy
        2. The command is executed successfully
        3. The output mentions that the upload URL connection was suuccessful
        4. The output mentions that the API URL connection test was successful
    """
    url_test = "End Upload URL Connection Test: SUCCESS"
    api_test = "End API URL Connection Test: SUCCESS"

    auth_proxy: str = (
        "http://"
        + test_config.get("auth_proxy", "username")
        + ":"
        + test_config.get("auth_proxy", "password")
        + "@"
        + test_config.get("auth_proxy", "host")
        + ":"
        + str(test_config.get("auth_proxy", "port"))
    )
    insights_client.config.proxy = auth_proxy
    insights_client.config.save()
    test_connection = insights_client.run("--test-connection")
    assert url_test in test_connection.stdout
    assert api_test in test_connection.stdout


def test_wrong_url_connection(insights_client):
    """
    :id: aa411b34-9af2-4759-ae05-756e9019c85e
    :title: Test wrong URL connection
    :description:
        Verifies that the insights-client fails to connect when an
        incorrect URL is configured
    :tier: Tier 1
    :steps:
        1. Disable auto-configuration and auto-updates
        2. Set an incorrect base URL in the configuration
        3. Run insights-client with the --test-connection option
        4. Verify the command fails due to the incorrect URL
        5. Check that the output contains the appropriate failure message
    :expectedresults:
        1. Auto-configuration and auto-updates are disabled
        2. Incorrect base URL is set
        3. Insights-client command is executed successfully
        4. The command failed with a return code of 1
        5. The message includes expected mentions of the failure
    """
    end_upload_failure = "Failed to establish a new connection"
    failed_connectivity_test = "Connectivity test failed!"

    insights_client.config.auto_config = False
    insights_client.config.auto_update = False
    insights_client.config.base_url = "no-such-insights-url.example.com/something"
    insights_client.config.authmethod = "CERT"
    insights_client.config.save()

    test_connection = insights_client.run("--test-connection", check=False)
    assert test_connection.returncode == 1
    assert end_upload_failure in test_connection.stdout
    assert failed_connectivity_test in test_connection.stdout
