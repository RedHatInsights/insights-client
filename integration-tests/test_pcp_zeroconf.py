"""
:casecomponent: insights-client
:requirement: RHSS-291297
:polarion-project-id: RHELSS
:polarion-include-skipped: false
:polarion-lookup-method: id
:subsystemteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import pytest
import subprocess
import conftest
from constants import CONFIG_FILE

pytestmark = pytest.mark.usefixtures("register_subman")

PACKAGE = "pcp-zeroconf"
SERVICE = "pmlogger"


@pytest.mark.tier1
def test_pcp_zeroconf_install():
    """
    :id: c8f92de7-4402-47b1-a718-7eb98c5c2915
    :title: Verify pcp-zeroconf can be installed
    :description:
        Ensure that the pcp-zeroconf can be successfully installed
    :tags: Tier 1
    :steps:
        1. Try to install pcp-zeroconf package
        2. Verify pmlogger service is running
        3. Check that auto_update is set to True
            in /etc/insights-client/insights-client.conf
    :expectedresults:
        1. Pcp-zeroconf package is installed
        2. Pmlogger service is active and running
        3. Auto_update is set to True in /etc/insights-client/insights-client.conf
    """
    install = subprocess.run(
        ["dnf", "install", "-y", "--disablerepo", "beaker-tasks", PACKAGE],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    assert install.returncode == 0, f"{PACKAGE} was not installed: {install.stderr}"

    pmlogger_status = subprocess.run(
        [SERVICE],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    service_not_found = f"{SERVICE}: command not found"
    assert service_not_found not in pmlogger_status.stderr, service_not_found

    grep_result = subprocess.run(
        ["pcp", "|", "grep", SERVICE],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=True,
    )
    assert grep_result.returncode == 0, f"{SERVICE} is not running"

    cat_result = subprocess.run(
        ["cat", CONFIG_FILE],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    assert "auto_update=True" in cat_result.stdout


@pytest.mark.tier1
def test_pmlogger_running_and_metrics_exist():
    """
    :id: 1b11a89d-1010-41c5-8641-51e0cd3f672f
    :title: Verify that pmlogger can be started and metrics exist
    :description:
        Ensure that the pmlogger service is active or can be activated.
    :tags: Tier 1
    :steps:
        1. Check the status of pmlogger service
        2. If not active, start the pmlogger service
    :expectedresults:
        1. Pmlogger service status is checked
        2. Pmlogger service is started if it was not active
        3. Pmlogger service is confirmed to be active
    """
    status_result = subprocess.run(
        ["systemctl", "is-active", SERVICE],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if status_result.stdout.strip() != "active":
        subprocess.run(["systemctl", "start", SERVICE], check=True)
        status_result = subprocess.run(
            ["systemctl", "is-active", SERVICE],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
    assert status_result.stdout.strip() == "active", f"{SERVICE} is not active"


@pytest.mark.tier1
def test_register_with_pcp(insights_client):
    """
    :id: 165a042a-87d0-44ff-8360-5954a4af895b
    :title: Test client registration
    :description:
        This test verifies that the --register command successfully registers
        an unregistered client with pcp-zeroconf installed and active
    :tags: Tier 1
    :steps:
        1. Run insights-client with --register
    :expectedresults:
        1. Verify the client successfully registered
    """
    register_result = insights_client.run("--register")
    assert conftest.loop_until(lambda: insights_client.is_registered)
    assert register_result.returncode == 0


@pytest.mark.tier1
def test_cleanup_pmlogger_and_pcp():
    """
    :id: bf492b14-3f57-4315-b8fb-7f0a1dd89cc6
    :title: Test cleanup of pmlogger and pcp
    :description:
        This test verifies that the pmlogger service can be stopped
        and the pcp-zeroconf package can be uninstalled.
    :tags: Tier 1
    :steps:
        1. Stop the pmlogger service
        2. Uninstall the pcp-zeroconf package
    :expectedresults:
        1. Pmlogger service is stopped
        2. Pcp-zeroconf package is uninstalled
    """

    # Stop pmlogger service
    stop_result = subprocess.run(
        ["systemctl", "stop", SERVICE],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    assert (
        stop_result.returncode == 0
    ), f"Failed to stop {SERVICE}: {stop_result.stderr}"

    # Uninstall pcp-zeroconf package
    uninstall_result = subprocess.run(
        ["dnf", "remove", "-y", PACKAGE],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    assert (
        uninstall_result.returncode == 0
    ), f"Failed to uninstall {PACKAGE}: {uninstall_result.stderr}"
