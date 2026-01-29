import datetime
import pytest
import subprocess
import logging

from selinux import SELinuxAVCChecker
from pytest_client_tools.util import loop_until

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
def check_avcs(request):
    """
    Monitor SELinux AVCs during the test execution.
    This fixture is applied to all tests and can be configured following way:
     * Skipping all SELinux AVCs (only logging them):
        Use this fixture explicitly by the test (adding `check_avcs` to test arguments)
        and then at the beginning of the test call: `check_avcs.skip_all_avcs()`
     * Skipping selected SELinux AVCs (only logging them)
        Use this fixture explicitly by the test (adding `check_avcs` to test arguments)
        and then at the beginning of the test call one of `SELinuxAVCChecker` skip methods.

    This pytest fixture yields instance of SELinuxAVCChecker class.
    """
    with SELinuxAVCChecker() as checker:
        # WORKAROUND: Wait for important services to finish be finished before running
        # the test to ensure stable environment. If the services are not finished and
        # the test starts, it may very easily happen, that the test starts touching
        # files used by the service bringing the system to undefined state eventually
        # also raising unexpected SELinux AVCs. This waiting should not belong here
        # and should be implemented somehow differently "the pytest way".
        wait_for_services_to_finish()
        yield checker
        # WORKAROUND: Wait for the services that are implicitly part of the test
        # to finish in order to ensure that all the operations done by those services
        # are monitored for the SELinux AVCs. The tests generally do not care about
        # status of services. It is crucial for the SELinux AVCs monitoring to
        # capture all events even those that happen on the background to be able to
        # associate those SELinux AVCs to the relevant tests during which those AVCs
        # occurred.
        wait_for_services_to_finish()
    logger.info(
        "All AVCs detected during test execution:\n"
        + "\n".join([str(denial) for denial in checker.get_avcs(skiplisted=False)])
    )
    denials = tuple(checker.get_avcs())
    if denials:
        pytest.fail(
            "AVCs detected during test run!\n" + "\n".join([str(denial) for denial in denials])
        )
