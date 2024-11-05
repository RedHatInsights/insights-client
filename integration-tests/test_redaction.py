"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: sst_csi_client_tools
:caseautomation: Automated
:upstream: Yes
"""

import pytest
import subprocess
import tarfile
import os
import yaml
import uuid
from enum import Enum

pytestmark = pytest.mark.usefixtures("register_subman")
TEST_CMD = ["/usr/bin/uptime", "/sbin/lsmod", "/bin/ls", "/sbin/ethtool"]
TEST_FILE = ["/proc/cpuinfo", "/proc/meminfo", "/etc/os-release"]
FILE_REDACTION_FILE = "/etc/insights-client/file-redaction.yaml"
CONTENT_REDACTION_FILE = "/etc/insights-client/file-content-redaction.yaml"


@pytest.mark.parametrize("not_removed_command", TEST_CMD)
def test_redaction_not_on_cmd(insights_client, tmp_path, not_removed_command):
    """
    :id: 264d1d8f-47a5-49ce-800c-d349aaacdb01
    :title: Test commands are collected when redaction not configured
    :description:
        This test verifies that when no commands are configured for redaction in
        `/etc/insights-client/file-redaction.yaml`, the outputs of the related
        commands are included in the collection archive
    :reference:
    :tags: Tier 1
    :steps:
        1. Ensure no command redaction is configured
        2. Run the insights client to collect data
        3. Check the archive for the specified command output
    :expectedresults:
        1. No commands are specified for redaction in the configuration file
        2. Data collection completes successfully
        3. The output of the command is present in the archive
    """
    assert check_archive(insights_client, tmp_path, not_removed_command)


@pytest.mark.parametrize("removed_command", TEST_CMD)
def test_redaction_on_cmd(insights_client, tmp_path, removed_command):
    """
    :id: a2d7b71c-205d-4545-8a6b-b0be9ff57611
    :title: Test commands are redacted when configured
    :description:
        This test verifies that when commands are configured for redaction in
        `/etc/insights-client/file-redaction.yaml`, the outputs of the related
        commands are excluded from the collection archive
    :reference:
    :tags: Tier 1
    :steps:
        1. Configure command redaction for the specified command
        2. Run the insights client to collect data
        3. Check the archive for the specified command output
        4. Clean up by removing the redaction configuration file
    :expectedresults:
        1. The command is added to the redaction configuration successfully
        2. Data collection completes successfully
        3. The output of the command is not present in the archive
        4. Configuration file is removed successfully
    """
    try:
        configure_file_redaction("Command", removed_command)
        assert not check_archive(insights_client, tmp_path, removed_command)
    finally:
        os.remove(FILE_REDACTION_FILE)


@pytest.mark.parametrize("not_removed_file", TEST_FILE)
def test_redaction_not_on_file(insights_client, tmp_path, not_removed_file):
    """
    :id: cb2ee8b8-fd82-48ad-bebc-3e044f277c55
    :title: Test files are collected when redaction not configured
    :description:
        This test verifies that when no files are configured for redaction in
        `/etc/insights-client/file-redaction.yaml`, the related files are
        included in the collection archive
    :reference:
    :tags: Tier 1
    :steps:
        1. Ensure no file redaction is configured
        2. Run the insights client to collect data
        3. Check the archive for the specified file
    :expectedresults:
        1. No files are specified for redaction in the configuration file
        2. Data collection completes successfully
        3. The file is present in the archive
    """
    assert check_archive(insights_client, tmp_path, not_removed_file)


@pytest.mark.parametrize("removed_file", TEST_FILE)
def test_redaction_on_file(insights_client, tmp_path, removed_file):
    """
    :id: 849cc4ac-d45e-44b8-b307-797935085eda
    :title: Test files are redacted when configured
    :description:
        This test verifies that when files are configured for redaction in
        `/etc/insights-client/file-redaction.yaml`, the related files are
        excluded from the collection archive
    :reference:
    :tags: Tier 1
    :steps:
        1. Configure file redaction for the specified file
        2. Run the insights client to collect data
        3. Check the archive for the specified file
        4. Clean up by removing the redaction configuration file
    :expectedresults:
        1. The file is added to the redaction configuration successfully
        2. Data collection completes successfully
        3. The file is not present in the archive
        4. Configuration file is removed successfully
    """
    try:
        configure_file_redaction("File", removed_file)
        assert not check_archive(insights_client, tmp_path, removed_file)
    finally:
        os.remove(FILE_REDACTION_FILE)


def test_redaction_on_pattern_hostname(insights_client, tmp_path):
    """
    :id: 641edf11-ace1-4a98-9fb4-198cf9e5e4d0
    :title: Test hostname is redacted when pattern is configured
    :description:
        This test verifies that when a pattern matching the system's
        hostname is configured for content redaction in
        `/etc/insights-client/content-redaction.yaml`, the hostname is
        obfuscated in the collected data
    :reference: https://issues.redhat.com/browse/RHEL-2471
    :tags: Tier 1
    :steps:
        1. Record the current system hostname
        2. Set a new hostname for testing
        3. Configure content redaction for the test hostname
        4. Run the insights client and collect data
        5. Check the archive to verify the hostname is redacted
        6. Restore the original hostname and clean up
    :expectedresults:
        1. The current hostname is recorded successfully
        2. The system hostname is updated to the test hostname
        3. The test hostname is added to the content redaction configuration
        4. Data collection completes successfully
        5. The test hostname is not present in the collected data
        6. Original hostname is restored, and configuration files are removed
    """
    # Record the current hostname
    with open("/etc/hostname", "r") as f:
        previous_hostname = f.read().strip()

    try:
        # Set a new hostname
        hostname_to_test = "insights-client-host"
        set_hostname(hostname_to_test)
        cmd = ["hostnamectl", "status"]
        output = subprocess.check_output(cmd, universal_newlines=True)
        assert hostname_to_test in output

        # redaction on hostname:
        configure_content_redaction(hostname_to_test)

        # check the collection, if redaction pattern is filtered out
        archive_name = "test_archive_" + str(uuid.uuid4()) + ".tar.gz"
        archive_location = tmp_path / archive_name
        insights_client.run("--register", "--output-file=%s" % archive_location)
        with tarfile.open(archive_location, "r") as tar:
            for w_file in tar.getmembers():
                extracted_file = tar.extractfile(w_file)
                if extracted_file is not None:
                    file_content = extracted_file.read().decode()
                    assert hostname_to_test not in file_content

    finally:
        set_hostname(previous_hostname)
        os.remove(CONTENT_REDACTION_FILE)


def check_archive(insights_client, tmp_path, tested):
    archive_location = tmp_path / "test_archive.tar.gz"
    insights_client.run("--output-file=%s" % archive_location)
    check_file = "/" + tested.split("/")[-1]
    if check_file == "/ls":
        check_file = "/ls_"
    with tarfile.open(archive_location, "r") as tar:
        check_tested = [
            file_name for file_name in tar.getnames() if check_file in file_name
        ]
    return check_tested


def configure_file_redaction(type, redaction_string):
    redaction_type = Enum("redaction_type", ["Command", "File"])
    if type == redaction_type.Command.name:
        file_content = {"commands": [redaction_string]}
    elif type == redaction_type.File.name:
        file_content = {"files": [redaction_string]}
    with open(FILE_REDACTION_FILE, "w") as f:
        yaml.dump(file_content, f, default_flow_style=False)
    os.chmod(FILE_REDACTION_FILE, 0o600)


def configure_content_redaction(pattern_string):
    file_content = {"patterns": {"regex": [pattern_string]}}
    with open(CONTENT_REDACTION_FILE, "w") as f:
        yaml.dump(file_content, f, default_flow_style=False)
    os.chmod(CONTENT_REDACTION_FILE, 0o600)


def set_hostname(hostname_to_set):
    cmd = ["hostnamectl", "set-hostname", hostname_to_set]
    subprocess.check_call(cmd)
