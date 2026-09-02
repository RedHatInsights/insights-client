import pytest
import subprocess
import logging
import cloud_inventory

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def _skip_when_cloud_inventory_unavailable(request):
    """Skip remaining requires_cloud_inventory tests after a session probe failure."""
    if request.node.get_closest_marker("requires_cloud_inventory") is None:
        yield
        return
    cloud_inventory.skip_if_auth_unavailable()
    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Reclassify check_* fixture "teardown"/"setup" failures as FAIL (instead of ERROR) by
    setting the test execution phase to "call" instead of "setup"/"teardown".
    """
    outcome = yield
    rep = outcome.get_result()
    if call.when == "call" or not call.excinfo:
        return
    if not isinstance(call.excinfo.value, pytest.fail.Exception):
        return

    for entry in call.excinfo.traceback:
        if getattr(entry, "name", "").startswith("check_"):
            rep.when = "call"
            return


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
