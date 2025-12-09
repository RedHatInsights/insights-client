import pytest
import subprocess
import logging

logger = logging.getLogger(__name__)


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
