"""
:component: insights-client
:requirement: RHSS-291297
:polarion-project-id: RHELSS
:polarion-include-skipped: false
:polarion-lookup-method: id
:poolteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import configparser
import contextlib
import logging
import os
import typing

import pytest

if typing.TYPE_CHECKING:
    import pytest_client_tools.insights_client

# the tests need a valid connection to insights so therefore the subman registration
pytestmark = pytest.mark.usefixtures("register_subman")


def _is_using_proxy(
    insights_config: "pytest_client_tools.insights_client.InsightsClientConfig",
) -> bool:
    for key, value in os.environ.items():
        if key.lower() == "https_proxy":
            logging.debug(f"Proxy is set via environment variable: '{value}'.")
            return True

    with contextlib.suppress(KeyError):
        insights_proxy: str = insights_config.proxy
        if insights_proxy != "":
            logging.debug(f"Proxy is set via insights-client: '{insights_proxy}'.")
            return True

    # sub-man fixture doesn't currently support reading the configuration file,
    # let's parse it ourselves.
    with contextlib.suppress(Exception):
        rhsm_config = configparser.ConfigParser()
        rhsm_config.read("/etc/rhsm/rhsm.conf")
        rhsm_proxy: str = rhsm_config.get("server", "proxy_hostname", fallback="")
        if rhsm_proxy != "":
            logging.debug(f"Proxy is set via subscription-manager: '{rhsm_proxy}'.")
            return True

    logging.debug("Proxy is not set.")
    return False


@pytest.mark.tier1
def test_connection_ok(insights_client):
    """
    :id: ff674d37-0ccc-481c-9f04-91237b8c50d0
    :title: Test connection
    :description:
        This test verifies that the --test-connection option works
        properly, confirming successful connection
    :tags: Tier 1
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


@pytest.mark.tier1
def test_http_timeout(insights_client):
    """
    :id: 46c5fe2a-1553-4f2e-802d-fa10080c72df
    :title: Test HTTP timeout configuration
    :description:
        Verifies that setting a very low http_timeout value causes
        the connection to time out
    :tags: Tier 1
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
    insights_client.config.http_timeout = 0.001
    insights_client.config.save()

    output = insights_client.run("--test-connection", check=False)
    assert output.returncode == 1

    if _is_using_proxy(insights_client.config):
        assert "timeout('timed out')" in output.stdout
    else:
        assert "Read timed out. (read timeout=0.001)"
    assert "Traceback" not in output.stdout


@pytest.mark.tier1
def test_noauth_proxy_connection(insights_client, test_config):
    """
    :id: a4bcb7e6-c04f-49d2-8362-525124dc61d9
    :title: Test no-auth proxy connection
    :description:
        Verifies that the insights-client can successfully connect
        through a no-auth proxy when using the --test-connection option
    :tags: Tier 1
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


@pytest.mark.tier1
def test_auth_proxy_connection(insights_client, test_config):
    """
    :id: 0b3e91d6-3b8b-42c7-8f3b-f7ee1728c311
    :title: Test auth-proxy connection
    :description:
        Verifies that the insights-client can successfully connect
        through an authenticated proxy
    :tags: Tier 1
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


@pytest.mark.tier1
def test_wrong_url_connection(insights_client):
    """
    :id: aa411b34-9af2-4759-ae05-756e9019c85e
    :title: Test wrong URL connection
    :description:
        Verifies that the insights-client fails to connect when an
        incorrect URL is configured
    :tags: Tier 1
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
    insights_client.config.auto_config = False
    insights_client.config.auto_update = False
    insights_client.config.base_url = "no-such-insights-url.example.com/something"
    insights_client.config.authmethod = "CERT"
    insights_client.config.save()

    test_connection = insights_client.run("--test-connection", check=False)
    assert test_connection.returncode == 1

    if _is_using_proxy(insights_client.config):
        assert "Cannot connect to proxy." in test_connection.stdout
    else:
        assert "Failed to establish a new connection" in test_connection.stdout
        assert "Connectivity test failed!" in test_connection.stdout
