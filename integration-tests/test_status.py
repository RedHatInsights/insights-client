import contextlib
import pytest
from time import sleep
import conftest

pytestmark = pytest.mark.usefixtures("register_subman")


def test_status_registered(external_candlepin, insights_client):
    """
    Test `insights-client --status` when the client is registered;
    in case of legacy_upload status command returns a different output.
    """
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)
    # Adding a small wait to ensure inventory is up-to-date
    sleep(5)
    registration_status = insights_client.run("--status")
    if insights_client.config.legacy_upload:
        assert "Insights API confirms registration." in registration_status.stdout
    else:
        assert "This host is registered.\n" == registration_status.stdout


def test_status_unregistered(external_candlepin, insights_client):
    """
    Test `insights-client --status` when the client is unregistered;
    in case of legacy_upload status command returns a different output.
    """
    # running unregistration to ensure system is unregistered
    with contextlib.suppress(Exception):
        insights_client.unregister()
    assert conftest.loop_until(lambda: not insights_client.is_registered)

    registration_status = insights_client.run("--status", check=False)
    if insights_client.config.legacy_upload:
        assert registration_status.returncode == 1
        assert (
            "Insights API says this machine is NOT registered."
            in registration_status.stdout
        )
    else:
        assert registration_status.returncode == 0
        assert "This host is unregistered.\n" == registration_status.stdout
