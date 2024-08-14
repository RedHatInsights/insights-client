"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: sst_csi_client_tools
:caseautomation: Automated
:upstream: Yes
"""

import json
import tarfile
import pytest
from constants import HOST_DETAILS
from constants import MACHINE_ID_FILE
import conftest


pytestmark = pytest.mark.usefixtures("register_subman")


def test_file_workflow_with_an_archive_with_only_one_canonical_fact(
    insights_client, tmp_path
):
    """
    :id: 816e341e-2477-4f24-8e37-dacf308413f5
    :title: Test File Workflow with an Archive with only One Canonical Fact
    :description:
        Verify uploading an Insights Archive with just one
        canonical fact creates a new host on Inventory
    :tier: Tier 1
    :steps:
        1. Remove canonical facts files from the pre-collected archive
            except the file that has the insights-id
        2. Upload the pre-collected archive
        3. Retrieve the system from Inventory
    :expectedresults:
        1. The facts are removed
        2. The pre-collected archive is successfully uploaded
        3. The host FQDN returned in host data retrieved from Inventory on step 3
            matches the hostname set in the archive
    """
    archive_name = tmp_path / "archive.tar.gz"
    modified_archive = tmp_path / "archive_modified.tar.gz"

    insights_client.run(f"--output-file={archive_name}")
    # Sending archive only with Insights ID
    files_to_remove = [
        "/data/etc/machine-id",
        "/data/insights_commands/hostname",
        "/data/insights_commands/hostname_-f",
        "/data/insights_commands/subscription-manager_identity",
    ]
    machine_id = open(MACHINE_ID_FILE, "r").read()
    remove_files_from_archive(archive_name, files_to_remove, modified_archive)
    upload_result = insights_client.run(
        f"--payload={modified_archive}", "--content-type=gz", check=False
    )
    assert "Successfully uploaded report" in upload_result.stdout

    # once archive is uploaded system status changes to register
    assert conftest.loop_until(lambda: insights_client.is_registered)

    insights_client.run("--check-results")  # to get host details from inventory
    with open(HOST_DETAILS, "r") as data_file:
        file_content = json.load(data_file)
        host_data = file_content["results"][0]

    assert host_data["insights_id"] == machine_id
    assert host_data["fqdn"] is None


def test_file_workflow_with_an_archive_without_canonical_facts(
    insights_client, tmp_path
):
    """
    :id: 46428b70-7803-4fb6-b694-66c88a0236e3
    :title: Test File Workflow with an Archive without Canonical Facts
    :description:
        Verify uploading an Insights Archive without canonical facts
        does NOT create a new host on Inventory
    :tier: Tier 1
    :steps:
        1. Remove all canonical facts files from the pre-collected archive
        2. Upload the pre-collected archive
        3. Validate that new host is not created in inventory
    :expectedresults:
        1. The facts are removed
        2. The pre-collected archive is successfully uploaded
        3. Host is not found in inventory
    """
    archive_name = tmp_path / "archive.tar.gz"
    modified_archive = tmp_path / "archive_modified.tar.gz"

    insights_client.run(f"--output-file={archive_name}")
    files_to_remove = [
        "/data/etc/insights-client/machine-id",
        "/data/etc/machine-id",
        "/data/etc/redhat-release",
        "/data/insights_commands/hostname",
        "/data/insights_commands/hostname_-f",
        "/data/insights_commands/subscription-manager_identity",
        "/data/insights_commands/dmidecode_-s_system-uuid",
        "/data/insights_commands/ip_addr",
        "/data/insights_commands/hostname_-I",
        "/data/sys/class/net/eth0/address",
        "/data/sys/class/net/lo/address",
    ]

    remove_files_from_archive(archive_name, files_to_remove, modified_archive)
    upload_result = insights_client.run(
        f"--payload={modified_archive}", "--content-type=gz", check=False
    )
    assert "Successfully uploaded report" in upload_result.stdout
    check_results = insights_client.run("--check-results", check=False)
    assert "Error: failed to find host with matching machine-id" in check_results.stdout


def remove_files_from_archive(original_archive, files_to_remove, modified_archive):
    with tarfile.open(original_archive, "r:gz") as tar:
        file_list = tar.getnames()
        dir_name = tar.getnames()[0]
        # append dirname to create absolute path names
        files_to_remove = [dir_name + item for item in files_to_remove]
        # Remove the specified files from the list
        files_to_keep = [f for f in file_list if f not in files_to_remove]
        # Create a new tar archive
        with tarfile.open(modified_archive, "w:gz") as new_tar:
            for member in tar.getmembers():
                if member.name in files_to_keep:
                    new_tar.addfile(member, tar.extractfile(member))
