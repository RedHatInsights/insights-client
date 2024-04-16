import pytest

# the tests need a valid connection to insights so therefore the subman registration
pytestmark = pytest.mark.usefixtures("register_subman")


def test_connection(insights_client):
    """
    Test insights-client --test-connection
    `test_connection` method returns 0 if success, 1 if failure
    """
    url_test = "End Upload URL Connection Test: SUCCESS"
    api_test = "End API URL Connection Test: SUCCESS"

    test_connection = insights_client.run("--test-connection")
    assert url_test in test_connection.stdout
    assert api_test in test_connection.stdout


def test_http_timeout(insights_client):
    """
    Test http_timeout config option
    Set http_timeout to a very low value, run --test-connection and check
    the set time
    """
    insights_client.config.http_timeout = 0.1
    insights_client.config.save()

    output = insights_client.run("--test-connection", check=False)
    assert output.returncode == 1
    assert "read timeout=0.1" in output.stdout


def test_noauth_proxy_connection(insights_client, test_config):
    """
    Test no-auth proxy option with --test-connection option
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
    Test auth proxy option with --test-connection
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
    Test wrong url option with --test-connection
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
