import os

import datetime
import pytest
import subprocess
import tempfile
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


@pytest.fixture(scope="session", autouse=True)
def insights_core_workaround():
    """
    Workaround for https://issues.redhat.com/browse/RHINENG-21918
    When insights-client is started by a user (running shell in unconfined mode)
    and the insights-client is run in insights_client_t SELinux context type
    (effectively switching the next python process that executes the insights_core
    code to insights_core_t SELinux context type), printing to PTY or pipe
    (through inherited file descriptor) that belongs to the user is not allowed.
    This Workaround fixture allows these actions in the active SELinux policy.
    """
    policy = """module core_output 1.0;

require {
  type insights_core_t;
  type unconfined_t;
  type user_devpts_t;
  class fifo_file write;
  class chr_file { ioctl read write };
}

#============= insights_core_t ==============
allow insights_core_t unconfined_t:fifo_file write;
allow insights_core_t user_devpts_t:chr_file { ioctl read write };
"""
    origdir = os.getcwd()
    with tempfile.TemporaryDirectory() as tempdirname:
        try:
            os.chdir(tempdirname)
            with open("core_output.te", "wt") as selinux_file:  # codespell:ignore te
                selinux_file.write(policy)
            subprocess.run(
                [
                    "checkmodule",
                    "-M",
                    "-m",
                    "-o",
                    "core_output.mod",
                    "core_output.te",  # codespell:ignore te
                ],
                check=True,
            )
            subprocess.run(
                ["semodule_package", "-o", "core_output.pp", "-m", "core_output.mod"],
                check=True,
            )
            subprocess.run(
                ["semodule", "-i", "core_output.pp"],
                check=True,
            )
        finally:
            os.chdir(origdir)
    yield
    subprocess.run(["semodule", "-r", "core_output"], check=True)


@pytest.fixture(autouse=True)
def check_no_egg_content():
    """
    Check that there is no egg-based content on the system.
    """
    yield
    egg_based_directory = "/var/lib/insights/"
    allowed_files = [
        "private-keys-v1.d",
        "pubring.kbx",
        "pubring.kbx~",
        "trustdb.gpg",
        "host-details.json",
    ]
    for name in os.listdir(egg_based_directory):
        if name not in allowed_files:
            pytest.fail(f"Unexpected additional content found: {name} in {egg_based_directory}")

    egg_based_files = [
        "/etc/insights-client/redhattools.pub.gpg",
        "/etc/insights-client/rpm.egg",
        "/etc/insights-client/rpm.egg.asc",
        "/etc/insights-client/.insights-core.etag",
        "/etc/insights-client/.insights-core-gpg-sig.etag",
    ]
    for file_path in egg_based_files:
        if os.path.exists(file_path):
            pytest.fail(f"File {file_path} should not exist on the system.")


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


def add_known_avcs_to_skiplist(avc_checker):
    avc_checker.skip_avc_entry_by_fields(
        {
            "subj": "system_u:system_r:insights_client_t:s0",
            "syscall": "openat",
            "permission": "search",
            "obj": "unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023",
        }
    )  # Bug: https://issues.redhat.com/browse/CCT-2009
    avc_checker.skip_avc_entry_by_fields(
        {
            "subj": "system_u:system_r:insights_client_t:s0",
            "syscall": "fstat",
            "permission": "getattr",
            "obj": "unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023",
        }
    )  # Bug: https://issues.redhat.com/browse/CCT-2009


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
        add_known_avcs_to_skiplist(checker)
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
