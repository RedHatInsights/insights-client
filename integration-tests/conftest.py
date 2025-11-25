import os
import pytest
import subprocess
import tempfile
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
def register_subman(
    external_candlepin, install_katello_rpm, subman_session, test_config
):
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
            not bootc_status.stdout.strip().startswith(
                "System is not deployed via bootc"
            )
        )
    except FileNotFoundError:
        return False


@pytest.fixture(autouse=True)
def check_avcs():
    checkpoint_file = f"/tmp/avc_checkpoint.{os.getpid()}"
    subprocess.run(
        ['ausearch', '-m', 'AVC', '--checkpoint', checkpoint_file],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    yield
    avcs = subprocess.run(
        ['ausearch', '-m', 'AVC', '--checkpoint', checkpoint_file],
        stdout=subprocess.PIPE,
    )
    if avcs.stdout:
        pytest.fail(
            "AVCs detected during test run!\n" +
            avcs.stdout.decode(),
        )

@pytest.fixture(autouse=True)
def use_selinux_permissive_mode():
    subprocess.run(['setenforce', 'permissive'], check=True)
    yield
