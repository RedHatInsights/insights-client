import pytest
import subprocess
import logging

from selinux import SELinuxAVCChecker

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
        yield checker
    logger.info(
        "All AVCs detected during test execution:\n"
        + "\n".join([str(denial) for denial in checker.get_avcs(skiplisted=False)])
    )
    denials = tuple(checker.get_avcs())
    if denials:
        pytest.fail(
            "AVCs detected during test run!\n" + "\n".join([str(denial) for denial in denials])
        )
