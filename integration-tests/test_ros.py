"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import pytest
import subprocess
import conftest
import shutil
from constants import CONFIG_FILE
from pathlib import Path

pytestmark = pytest.mark.usefixtures("register_subman")

PACKAGE = "insights-client-ros"
SERVICE = "pmlogger"


@pytest.mark.tier1
def test_ros_install():
    """
    :id: 3fc19957-be97-429d-817a-610e6c69dd9d
    :title: Verify insights-client-ros can be installed
    :description:
        Ensure that the insights-client-ros can be successfully installed
    :tags: Tier 1
    :steps:
        1. Try to install insights-client-ros
        2. Check that ros_collect is set to true in insights-client.conf
    :expectedresults:
        1. Subpackage insights-client-ros is installed
        2. Field ros_collect is set to true in insights-client.conf
    """
    install = subprocess.run(
        ["dnf", "install", "-y", PACKAGE], capture_output=True, text=True
    )
    assert install.returncode == 0, f"{PACKAGE} was not installed"

    cat_result = subprocess.run(["cat", CONFIG_FILE], capture_output=True, text=True)
    assert "ros_collect=True" in cat_result.stdout


@pytest.mark.tier1
def test_pmlogger_running_and_metrics_exist():
    """
    :id: 8b37e4b2-d873-4ef5-87f0-ba51ba33e3af
    :title: Verify that pmlogger can be started and metrics exist
    :description:
        Ensure that the pmlogger service is active or can be activated
        and that PCP metrics archives are present for the current hostname
    :tags: Tier 1
    :steps:
        1. Check pmlogger status using systemctl
        2. Check that the directory /var/log/pcp/pmlogger/<hostname> exists
    :expectedresults:
        1. Service is active. If not, it can be started
        2. Directory exists with metrics archives ending in .0
    """
    status_result = subprocess.run(
        ["systemctl", "is-active", SERVICE], capture_output=True, text=True
    )
    if status_result.stdout.strip() != "active":
        subprocess.run(["systemctl", "start", SERVICE], check=True)
        status_result = subprocess.run(
            ["systemctl", "is-active", SERVICE], capture_output=True, text=True
        )
    assert status_result.stdout.strip() == "active", f"{SERVICE} is not active"

    hostname = subprocess.run(
        ["hostname"], capture_output=True, text=True
    ).stdout.strip()
    metrics_dir = Path(f"/var/log/pcp/pmlogger/{hostname}")
    assert metrics_dir.exists(), f"{metrics_dir} does not exist"
    archives = list(metrics_dir.glob("*.0"))
    assert archives, f"No newest archives found in {metrics_dir}"


@pytest.mark.tier1
def test_register_with_ros(insights_client):
    """
    :id: 66b43a68-218f-4988-9f91-ac228d6cc19b
    :title: Test client registration
    :description:
        This test verifies that the --register command successfully registers
        an unregistered client with insights-client-ros installed and active
    :tags: Tier 1
    :steps:
        1. Run insights-client with --register option
    :expectedresults:
        1. Verify the client successfully registered
    """
    register_result = insights_client.run("--register")
    assert conftest.loop_until(lambda: insights_client.is_registered)
    assert register_result.returncode == 0


@pytest.mark.tier2
def test_upload_pre_collected_archive_with_ros(insights_client, tmp_path):
    """
    :id: 0f316a85-2e2b-45a1-8440-672d95dce02a
    :title: Test Upload of Pre-Collected Archive
    :description:
        This test verifies that a pre-collect insights-archive
        can be uploaded using --payload operation even with
        insights-client-ros active.
    :tags: Tier 2
    :steps:
        1. Register insights-client
        2. Run insights-client in an offline mode to generate an archive
            and save it
        3. Run the insights-client with the --payload option and valid --content-type
        4. Verify the successful upload of the archive
    :expectedresults:
        1. Insights-client is registered
        2. The archive is successfully generated and saved
        3. The upload process starts and the output message is as expected
        4. The upload completes successfully with the message as expected
    """
    archive_name = "archive.tar.gz"
    archive_location = tmp_path / archive_name

    # Registering the client because upload can happen on registered system
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    # Running insights-client in offline mode to generate archive and save at tmp dir
    insights_client.run(f"--output-file={archive_location}")

    # Running insights-client --payload with --content-type to upload archive
    # collected in previous step
    upload_result = insights_client.run(
        f"--payload={archive_location}", "--content-type=gz"
    )
    assert "Uploading Insights data." in upload_result.stdout
    assert "Successfully uploaded report" in upload_result.stdout


@pytest.mark.tier1
def test_cleanup_pmlogger_and_ros():
    """
    :id: e9e150af-4fb7-42c2-b72b-5e1656959530
    :title: Verify insights-client-ros can be uninstalled
        and pmlogger can be stopped
    :description:
        This test verifies that the pmlogger service can be stopped and
        ROS can be uninstalled to clean up the system after testing ros
    :tags: Tier 1
    :steps:
        1. Stop the pmlogger service using systemctl
        2. Remove the ROS directory and uninstall insights-client-ros
    :expectedresults:
        1. Pmlogger service is stopped
        2. The directory is removed and insights-client-ros is uninstalled
    """
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

    # Remove the ROS directory
    ros_dir = Path("/var/log/pcp/pmlogger/ros")
    if ros_dir.exists():
        shutil.rmtree(ros_dir, ignore_errors=True)
    assert not ros_dir.exists(), "ROS directory still exists after removal"

    # Uninstall insights-client-ros
    uninstall_result = subprocess.run(
        ["dnf", "remove", "-y", PACKAGE], capture_output=True, text=True
    )
    assert (
        uninstall_result.returncode == 0
    ), f"Failed to uninstall {PACKAGE}: {uninstall_result.stderr}"
