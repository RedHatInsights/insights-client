import pytest
import subprocess
import tarfile
import os
import yaml
import uuid
from enum import Enum

pytestmark = pytest.mark.usefixtures("register_subman")
TEST_CMD = ["/usr/bin/uptime", "/sbin/lsmod", "/bin/ls", "/sbin/ethtool"]
TEST_FILE = ["/proc/cpuinfo", "/proc/meminfo", "/etc/yum.conf", "/etc/os-release"]
FILE_REDACTION_FILE = "/etc/insights-client/file-redaction.yaml"
CONTENT_REDACTION_FILE = "/etc/insights-client/file-content-redaction.yaml"


@pytest.mark.parametrize("not_removed_command", TEST_CMD)
def test_redaction_not_on_cmd(insights_client, tmp_path, not_removed_command):
    """
    Do not configure commands in /etc/insights-client/file-redaction.yaml,
    so related commands should exist in collection archive.
    """
    assert check_archive(insights_client, tmp_path, not_removed_command)


@pytest.mark.parametrize("removed_command", TEST_CMD)
def test_redaction_on_cmd(insights_client, tmp_path, removed_command):
    """
    Configure command redaction in /etc/insights-client/file-redaction.yaml,
    so related commands should not exist in collection archive.
    """
    try:
        configure_file_redaction("Command", removed_command)
        assert not check_archive(insights_client, tmp_path, removed_command)
    finally:
        os.remove(FILE_REDACTION_FILE)


@pytest.mark.parametrize("not_removed_file", TEST_FILE)
def test_redaction_not_on_file(insights_client, tmp_path, not_removed_file):
    """
    Do not configure files in /etc/insights-client/file-redaction.yaml,
    so related files should exist in collection archive.
    """
    assert check_archive(insights_client, tmp_path, not_removed_file)


@pytest.mark.parametrize("removed_file", TEST_FILE)
def test_redaction_on_file(insights_client, tmp_path, removed_file):
    """
    Redact files in /etc/insights-client/file-redaction.yaml,
    so related files should not exist in collection archive.
    """
    try:
        configure_file_redaction("File", removed_file)
        assert not check_archive(insights_client, tmp_path, removed_file)
    finally:
        os.remove(FILE_REDACTION_FILE)


def test_redaction_on_pattern_hostname(insights_client, tmp_path):
    """
    Test if the system hostname is obfuscated
    Related to https://issues.redhat.com/browse/RHEL-2471

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
