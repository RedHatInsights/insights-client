import datetime
import pytest
import subprocess
import logging
import cloud_inventory

from pytest_client_tools.util import loop_until
from insights_selinux import avc_skips_for_test

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def _skip_when_cloud_inventory_unavailable(request):
    """Skip remaining requires_cloud_inventory tests after a session probe failure."""
    if request.node.get_closest_marker("requires_cloud_inventory") is None:
        yield
        return
    cloud_inventory.skip_if_auth_unavailable()
    yield


@pytest.fixture
def client_tools_avc_skips(request):
    """Provide this project's known AVC exceptions to pytest-client-tools."""
    return avc_skips_for_test(request.node.name)


@pytest.fixture(scope="session")
def install_katello_rpm(test_config):
    if "satellite" in test_config.environment:
        # install katello rpm before register system against Satellite
        satellite_hostname = test_config.get("candlepin", "host")
        cmd = [
            "rpm",
            "-Uvh",
            "http://%s/pub/katello-ca-consumer-latest.noarch.rpm" % satellite_hostname,
        ]
        subprocess.check_call(cmd)
    yield
    if "satellite" in test_config.environment:
        cmd = "rpm -qa 'katello-ca-consumer*' | xargs rpm -e"
        subprocess.check_call(cmd, shell=True)


@pytest.fixture(scope="session")
def register_subman(external_candlepin, install_katello_rpm, subman_session, test_config):
    if "satellite" in test_config.environment:
        subman_session.register(
            activationkey=test_config.get("candlepin", "activation_keys"),
            org=test_config.get("candlepin", "org"),
        )
    else:
        subman_session.register(
            username=test_config.get("candlepin", "username"),
            password=test_config.get("candlepin", "password"),
        )
    yield subman_session


def check_is_bootc_system():
    """
    Check if the system is a bootc enabled system.
    This function duplicates the logic from pytest-client-tools' is_bootc_system fixture
    so it can be used in pytest.skipif decorators (which run at collection time).
    """
    try:
        bootc_status = subprocess.run(
            ["bootc", "status", "--format", "humanreadable"],
            capture_output=True,
            text=True,
        )
        return (bootc_status.returncode == 0) and (
            not bootc_status.stdout.strip().startswith("System is not deployed via bootc")
        )
    except FileNotFoundError:
        return False


def wait_for_services_to_finish(services=None):
    if services is None:
        services = (
            "insights-client.service",
            "insights-client-results.service",
        )
    logger.debug(f"{datetime.datetime.now()} Waiting for systemd services to finish: {services}")
    for service in services:
        if not loop_until(
            lambda: subprocess.run(["systemctl", "is-active", "--quiet", service]).returncode != 0
        ):
            logger.info(f"Systemd service is still running: {service}")
    logger.debug(f"{datetime.datetime.now()} Finished waiting for systemd services to finish")


@pytest.fixture(autouse=True)
def wait_for_services_during_avc_capture(check_avcs):
    """Keep client services inside the plugin's per-test AVC collection window."""
    wait_for_services_to_finish()
    yield
    wait_for_services_to_finish()
