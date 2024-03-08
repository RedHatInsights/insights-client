import os
import subprocess

import pytest


pytestmark = pytest.mark.usefixtures("register_subman")

MACHINE_ID_FILE: str = "/etc/insights-client/machine-id"


def test_machineid_exists_only_when_registered(insights_client):
    """`machine-id` is only present when insights-client is registered."""
    assert not insights_client.is_registered
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

    assert machine_id_new != machine_id_old


def test_double_registration(insights_client):
    """`--register` can be passed multiple times.

    Even system that is already registered should allow the `--register` flag to be
    passed in, without resulting in non-zero exit code.

    This behavior has changed multiple times during the package lifetime.
    """
    assert not insights_client.is_registered

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
