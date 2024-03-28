import os
import contextlib
import pytest
import functools
import logging
from conftest import loop_until

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.usefixtures("register_subman")

MACHINE_ID_FILE: str = "/etc/insights-client/machine-id"


def test_register(insights_client):
    """
    Test `insights-client --register` when the client is registered
    """
    response = insights_client.run("--register", check=False)
    assert (
        response.returncode == 0
    ), "An application returns 0 after successful registration"
    assert (
        "Successfully registered host" in response.stdout
    ), "An application should inform a user that a system was registered"
    assert (
        "Starting to collect Insights data" in response.stdout
    ), "An application should inform a user that Insights data will be collected"
    assert (
        "Successfully uploaded report" in response.stdout
    ), "An application should inform a user that report was successfully uploaded"
    assert (
        "View the Red Hat Insights console" in response.stdout
    ), "An application should inform a user about Insights console"
    assert (
        insights_client.is_registered
    ), "Current state of registration should be 'registered'"


def test_double_register(insights_client):
    """`--register` can be passed multiple times.

    Even system that is already registered should allow the `--register` flag to be
    passed in, without resulting in non-zero exit code.

    This behavior has changed multiple times during the package lifetime.
    """
    assert not insights_client.is_registered

    insights_client.register()
    assert os.path.exists(
        MACHINE_ID_FILE
    ), f"{MACHINE_ID_FILE} should exist after successfull registration"

    with open(MACHINE_ID_FILE, "r") as f:
        machine_id_old = f.read()

    response = insights_client.register()
    assert (
        "This host has already been registered" in response.stdout
    ), "An application should inform that a system was already registered"
    assert (
        "Successfully uploaded report" in response.stdout
    ), "An application should inform that report was successfully uploaded"
    assert (
        "View the Red Hat Insights console" in response.stdout
    ), "An application should inform about Insights console"
    assert loop_until(
        lambda: insights_client.is_registered
    ), "Current state of registration should be 'registered'"

    assert os.path.exists(MACHINE_ID_FILE)

    with open(MACHINE_ID_FILE, "r") as f:
        machine_id_new = f.read()

    assert (
        machine_id_new == machine_id_old
    ), f"{MACHINE_ID_FILE} should remain the same after repeated registration"


def test_machineid_exists_only_when_registered(insights_client):
    """`machine-id` is only present when insights-client is registered."""
    assert not insights_client.is_registered
    assert not os.path.exists(MACHINE_ID_FILE)

    res = insights_client.run(check=False)
    assert (
        "This machine has not yet been registered. Use --register to register"
    ) in res.stdout, "An application should ask a user to register a system"
    assert res.returncode != 0
    assert not os.path.exists(MACHINE_ID_FILE)

    insights_client.register()
    assert os.path.exists(MACHINE_ID_FILE)

    insights_client.unregister()
    assert not os.path.exists(MACHINE_ID_FILE)


def test_machineid_changes_on_new_registration(insights_client):
    """machine-id content changes when insights-client is un- & registered."""
    insights_client.register()
    with open(MACHINE_ID_FILE, "r") as f:
        machine_id_old = f.read()

    insights_client.unregister()
    assert not os.path.exists(MACHINE_ID_FILE)

    insights_client.register()
    with open(MACHINE_ID_FILE, "r") as f:
        machine_id_new = f.read()

    assert machine_id_new != machine_id_old


def test_register_using_noauth_proxy(insights_client, test_config):
    proxy_config = functools.partial(test_config.get, "noauth_proxy")
    proxy = f'http://{proxy_config("host")}:{proxy_config("port")}'
    logger.debug(f"A test will use proxy service {proxy}")
    insights_client.config.proxy = proxy
    insights_client.config.save()
    insights_client.register()
    assert insights_client.is_registered

    with open("/var/log/insights-client/insights-client.log", "rt") as log:
        msg = f"insights.client.connection CONF Proxy: {proxy}"
        assert any(
            msg in line for line in log
        ), f"Message '{msg}' about using proxy should appear in a log file"


def test_register_using_auth_proxy(insights_client, test_config):
    # format of proxy property:
    #     http://user:pass@192.168.100.50:8080
    #
    proxy_config = functools.partial(test_config.get, "auth_proxy")
    proxy = "http://{}:{}@{}:{}".format(
        proxy_config("username"),
        proxy_config("password"),
        proxy_config("host"),
        proxy_config("port"),
    )
    logger.debug(f"A test will use proxy service {proxy}")
    insights_client.config.proxy = proxy
    insights_client.config.save()
    insights_client.run("--register")
    assert insights_client.is_registered

    with open("/var/log/insights-client/insights-client.log", "rt") as log:
        msg = "insights.client.connection CONF Proxy: http://{}:{}".format(
            proxy_config("host"), proxy_config("port")
        )
        assert any(
            msg in line for line in log
        ), f"Message '{msg}' about using proxy should appear in a log file"


@pytest.mark.parametrize(
    "legacy_upload_value",
    [
        pytest.param(True, marks=pytest.mark.xfail),
        pytest.param(False),
    ],
)
def test_register_group_option(insights_client, legacy_upload_value):
    """
    Bug https://issues.redhat.com/browse/RHINENG-7567 exists on both
    production env and satellite env with legacy_upload=True.
    With legacy_upload=False, "insights-client --register --group=tag"
    works well on both envs.
    """
    # make sure the system is not registered to insights
    with contextlib.suppress(Exception):
        insights_client.unregister()
    assert not insights_client.is_registered
    insights_client.config.legacy_upload = legacy_upload_value
    insights_client.config.save()
    register_group_option = insights_client.run(
        "--register",
        "--group=tag",
        check=False,
    )
    assert register_group_option.returncode == 0
