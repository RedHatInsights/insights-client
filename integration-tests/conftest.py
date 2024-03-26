import pytest
import subprocess
import time
import json
import requests
import logging

logger = logging.getLogger(__name__)

MACHINE_ID_FILE: str = "/etc/insights-client/machine-id"

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

def loop_until(pred, poll_sec=5, timeout_sec=60):
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
    
@pytest.fixture(scope="session")
def fetch_from_inventory(test_config):
    """
    curl https://<console_service_hostname>/api/inventory/v1/hosts?insights_id=<insights-client/machine_id> \
      --cert /etc/pki/consumer/cert.pem \
      --key /etc/pki/consumer/key.pem \
      -k
    """
    def _wrapper(insights_id=None):
        hostname = test_config.get("console", "host")
        if not insights_id:
            logger.info(f"{MACHINE_ID_FILE} will be used to fetch an inventory")
            with open(MACHINE_ID_FILE,"rt") as f:
                insights_id=f.read()
                
        response = requests.get(f"https://{hostname}/api/inventory/v1/hosts?insights_id={insights_id}",
                              cert=("/etc/pki/consumer/cert.pem","/etc/pki/consumer/key.pem"))
        print(response)
        return response.json()

    yield _wrapper
