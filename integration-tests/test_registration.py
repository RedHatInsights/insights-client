import os
import pytest
import contextlib
from pytest_client_tools.util import Version
import conftest


pytestmark = pytest.mark.usefixtures("register_subman")

MACHINE_ID_FILE: str = "/etc/insights-client/machine-id"


def test_machineid_exists_only_when_registered(insights_client):
    """`machine-id` is only present when insights-client is registered."""
    assert conftest.loop_until(lambda: not insights_client.is_registered)
    assert not os.path.exists(MACHINE_ID_FILE)

    res = insights_client.run(check=False)
    assert (
        "This host has not been registered. Use --register to register this host."
    ) in res.stdout
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

    if insights_client.core_version >= Version(3, 3, 16):
        """after the new changes to CCT-161 machine-id stays the same"""
        assert machine_id_new == machine_id_old
    else:
        assert machine_id_new != machine_id_old


def test_double_registration(insights_client):
    """`--register` can be passed multiple times.

    Even system that is already registered should allow the `--register` flag to be
    passed in, without resulting in non-zero exit code.

    This behavior has changed multiple times during the package lifetime.
    """
    assert conftest.loop_until(lambda: not insights_client.is_registered)

    insights_client.register()
    assert os.path.exists(MACHINE_ID_FILE)
    with open(MACHINE_ID_FILE, "r") as f:
        machine_id_old = f.read()

    res = insights_client.register()
    assert "This host has already been registered" in res.stdout
    assert os.path.exists(MACHINE_ID_FILE)
    with open(MACHINE_ID_FILE, "r") as f:
        machine_id_new = f.read()

    assert machine_id_new == machine_id_old


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
    assert conftest.loop_until(lambda: not insights_client.is_registered)
    insights_client.config.legacy_upload = legacy_upload_value
    insights_client.config.save()
    register_group_option = insights_client.run(
        "--register",
        "--group=tag",
        check=False,
    )
    assert register_group_option.returncode == 0


def test_registered_and_unregistered_files_are_created_and_deleted(insights_client):
    """'.registered and .unregistered file gets created and deleted"""
    assert conftest.loop_until(lambda: not insights_client.is_registered)
    assert not os.path.exists("/etc/insights-client/.registered")

    insights_client.register()
    assert os.path.exists("/etc/insights-client/.registered")
    assert not os.path.exists("/etc/insights-client/.unregistered")

    insights_client.unregister()
    assert os.path.exists("/etc/insights-client/.unregistered")
    assert not os.path.exists("/etc/insights-client/.registered")
