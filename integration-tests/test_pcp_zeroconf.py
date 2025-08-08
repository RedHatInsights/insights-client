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
    install = subprocess.run(
        ["dnf", "install", "-y", PACKAGE],
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
    register_result = insights_client.run("--register")
    assert conftest.loop_until(lambda: insights_client.is_registered)
    assert register_result.returncode == 0


@pytest.mark.tier1
def test_cleanup_pmlogger_and_pcp():

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

    # Verify pmlogger is inactive
    status_result = subprocess.run(
        ["systemctl", "is-active", SERVICE],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    assert (
        status_result.stdout.strip() != "active"
    ), f"{SERVICE} service is still active after stopping"

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
