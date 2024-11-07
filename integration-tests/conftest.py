import pytest
import subprocess
import time
from pytest_client_tools.util import logged_run


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


def loop_until(predicate, poll_sec=5, timeout_sec=120):
    """
    An helper function to handle a time periond waiting for an external service
    to update its state.

    an example:

       assert loop_until(lambda: insights_client.is_registered)

    The loop function will retry to run predicate every 5secs
    until the total time exceeds timeout_sec.
    """
    start = time.time()
    ok = False
    while (not ok) and (time.time() - start < timeout_sec):
        time.sleep(poll_sec)
        ok = predicate()
    return ok


@pytest.fixture(scope="session", autouse=True)
def collect_selinux_denials():
    """This fixture helps in catching selinux denials
    in the system after tests are run."""
    yield
    command = "ausearch -m avc -m user_avc -m selinux_err -i".split()
    result = logged_run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if "<no matches>" not in result.stdout:
        lines = result.stdout.split("\n")
        for line in lines:
            words = line.split()
            if "denied" in words:
                assert "permissive=1" in words, "SELinux AVC denials found"
