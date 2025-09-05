"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import json
import os
import random
import string
import subprocess
import tarfile
from time import sleep
import pytest
from constants import HOST_DETAILS
from constants import MACHINE_ID_FILE
import conftest
import logging


pytestmark = pytest.mark.usefixtures("register_subman")


@pytest.mark.tier1
def test_file_workflow_with_an_archive_with_only_one_canonical_fact(
    insights_client, tmp_path
):
    """
    :id: 816e341e-2477-4f24-8e37-dacf308413f5
    :title: Test File Workflow with an Archive with only One Canonical Fact
    :description:
        Verify uploading an Insights Archive with just one
        canonical fact creates a new host on Inventory
    :tags: Tier 1
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
    modify_archive(archive_name, modified_archive, files_to_remove)
    upload_result = insights_client.run(
        f"--payload={modified_archive}", "--content-type=gz", check=False
    )
    assert "Successfully uploaded report" in upload_result.stdout

    # once archive is uploaded system status changes to register
    assert conftest.loop_until(lambda: insights_client.is_registered)

    insights_client.run("--check-results")  # to get host details from inventory
    with open(HOST_DETAILS, "r") as data_file:
        file_content = json.load(data_file)

    assert "count" in file_content.keys()
    assert file_content["count"] == 1
    assert "results" in file_content.keys()
    host_data = file_content["results"][0]

    assert host_data.get("insights_id") == machine_id


@pytest.mark.tier1
def test_file_workflow_with_an_archive_without_canonical_facts(
    insights_client, tmp_path
):
    """
    :id: 46428b70-7803-4fb6-b694-66c88a0236e3
    :title: Test File Workflow with an Archive without Canonical Facts
    :description:
        Verify uploading an Insights Archive without canonical facts
        does NOT create a new host on Inventory
    :tags: Tier 1
    :steps:
        1. Remove all canonical facts files from the pre-collected archive
        2. Upload the pre-collected archive
    :expectedresults:
        1. The facts are removed
        2. The pre-collected archive is successfully uploaded
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

    modify_archive(archive_name, modified_archive, files_to_remove)
    upload_result = insights_client.run(
        f"--payload={modified_archive}", "--content-type=gz", check=False
    )
    assert "Successfully uploaded report" in upload_result.stdout


@pytest.mark.skipif(
    "container" in os.environ.keys(),
    reason="Containers cannot change hostnames",
)
@pytest.mark.tier1
def test_file_workflow_archive_update_host_info(insights_client, external_inventory):
    """
    :id: 336abff9-4263-4f1d-9448-2cd05d40a371
    :title: Verify Insights Archive Updates Host Information
    :description:
        Ensure that updating files within an Insights Archive reflects
        the correct host information, such as hostname, in the Inventory
    :tags: Tier 1
    :steps:
        1. Register the system with insights-client and confirm data upload
        2. Change the system hostname
        3. Collect and upload the new archive
        4. Retrieve host data from Inventory and verify fqdn
    :expectedresults:
        1. The system is registered and the archive is uploaded successfully
        2. The system hostname is updated successfully
        3. A new archive is collected and uploaded successfully
        4. The fqdn in the Inventory matches the updated hostname
    """
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)
    current_hostname = subprocess.check_output("hostname", shell=True).decode().strip()

    # Set a new hostname
    new_hostname = set_hostname()
    fqdn = subprocess.check_output("hostname -f", shell=True).decode().strip()
    logging.debug(f"Assigned hostname: {new_hostname}, FQDN: {fqdn}")

    insights_client.run()
    sleep(30)  # Wait for data to get reflected in inventory
    host_data = external_inventory.this_system()
    logging.debug(f"Host data from inventory: {host_data}")

    # New hostname matches the one in Inventory
    assert host_data.get("fqdn") == fqdn

    # Reset to the original hostname
    set_hostname(current_hostname)


def modify_archive(
    original_archive, modified_archive, files_to_remove=None, files_to_add=None
):
    files_to_add = files_to_add or []
    files_to_remove = files_to_remove or []
    with tarfile.open(original_archive, "r:gz") as tar:
        file_list = tar.getnames()
        dir_name = tar.getnames()[0]
        # Append dirname to create absolute path names
        files_to_remove = [dir_name + item for item in files_to_remove]
        # Remove the specified files from the list
        files_to_keep = [f for f in file_list if f not in files_to_remove]
        # Create a new tar archive
        with tarfile.open(modified_archive, "w:gz") as new_tar:
            for member in tar.getmembers():
                if member.name in files_to_keep:
                    new_tar.addfile(member, tar.extractfile(member))
            # Add new files
            for file_path, arcname in files_to_add:
                new_tar.add(file_path, arcname=f"{dir_name}/{arcname}")


def set_hostname(hostname=None):
    if hostname is None:
        hostname = (
            "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
            + "-new-hostname.example.com"
        )

    subprocess.run(["hostnamectl", "set-hostname", hostname], check=True)
    return hostname
