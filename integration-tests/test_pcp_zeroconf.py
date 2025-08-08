"""
:component: insights-client
:requirement: RHSS-291297
:polarion-project-id: RHELSS
:polarion-include-skipped: false
:polarion-lookup-method: id
:poolteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import pytest
import subprocess
import conftest
from constants import CONFIG_FILE

PACKAGE = "pcp-zeroconf"
SERVICE = "pmlogger"


@pytest.mark.tier1
def test_pcp_zeroconf_install():
    install = subprocess.run(
        ["dnf", "install", "-y", PACKAGE], capture_output=True, text=True
    )
    assert install.returncode == 0, f"{PACKAGE} was not installed"

    pmlogger_status = subprocess.run(
        [SERVICE], capture_output=True, text=True
    )
    service_not_found = f"{SERVICE}: command not found"
    assert not service_not_found in pmlogger_status.stderr, service_not_found

    grep_result = subprocess.run(
        ["pcp", "|", "grep", SERVICE], capture_output=True, text=True, shell=True
    )
    assert grep_result.returncode == 0, f"{SERVICE} is not running"

    cat_result = subprocess.run(["cat", CONFIG_FILE], capture_output=True, text=True)
    assert "auto_update=True" in cat_result.stdout


@pytest.mark.tier1
def test_pmlogger_running_and_metrics_exist():
    status_result = subprocess.run(
        ["systemctl", "is-active", SERVICE], capture_output=True, text=True
    )
    if status_result.stdout.strip() != "active":
        subprocess.run(["systemctl", "start", SERVICE], check=True)
        status_result = subprocess.run(
            ["systemctl", "is-active", SERVICE], capture_output=True, text=True
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
        ["systemctl", "stop", SERVICE], capture_output=True, text=True
    )
    assert (
        stop_result.returncode == 0
    ), f"Failed to stop {SERVICE}: {stop_result.stderr}"

    # Verify pmlogger is inactive
    status_result = subprocess.run(
        ["systemctl", "is-active", SERVICE], capture_output=True, text=True
    )
    assert (
        status_result.stdout.strip() != "active"
    ), f"{SERVICE} service is still active after stopping"

    # Uninstall pcp-zeroconf package
    uninstall_result = subprocess.run(
        ["dnf", "remove", "-y", PACKAGE], capture_output=True, text=True
    )
    assert (
        uninstall_result.returncode == 0
    ), f"Failed to uninstall {PACKAGE}: {uninstall_result.stderr}"

