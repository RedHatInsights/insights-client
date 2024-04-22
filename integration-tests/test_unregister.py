import pytest
import conftest

pytestmark = pytest.mark.usefixtures("register_subman")


def test_unregister(insights_client):
    """Test insights-client --unregister after registering it

    If the unregistration is successful, `unregister` method returns True
    """
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    unregistration_status = insights_client.run("--unregister")
    assert (
        "Successfully unregistered from the Red Hat Insights Service"
        in unregistration_status.stdout
    )
    assert conftest.loop_until(lambda: not insights_client.is_registered)


def test_unregister_twice(insights_client):
    """Test insights-client --unregister on unregistered system
    If the unregistration is successful, `--unregister` returns True on first attempt
    and false on subsequent attempts."""

    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    # unregister once
    unregistration_status = insights_client.run("--unregister")
    assert conftest.loop_until(lambda: not insights_client.is_registered)
    assert (
        "Successfully unregistered from the Red Hat Insights Service"
        in unregistration_status.stdout
    )
    # unregister twice
    unregistration_status = insights_client.run("--unregister", check=False)
    assert conftest.loop_until(lambda: not insights_client.is_registered)
    assert unregistration_status.returncode == 1
    assert (
        "This host is not registered, unregistration is not applicable."
        in unregistration_status.stdout
    )
