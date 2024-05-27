import pytest
import subprocess
import time


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


def loop_until(pred, poll_sec=5, timeout_sec=90):
    """
    An helper function to handle a time periond waiting for an external service
    to update its state.

    an example:

       result = loop_until(lambda: insights_client.is_registered)
       assert result == True

    The loop function will retry to run predicate every 5secs
    untill the total time exceeds timeout_sec.
    """
    start = time.time()
    ok = False
    while (not ok) and (time.time() - start < timeout_sec):
        time.sleep(poll_sec)
        ok = pred()
    return ok
