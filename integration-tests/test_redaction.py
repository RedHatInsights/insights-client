import pytest
import subprocess
from time import sleep
import re
import tarfile
import os
import contextlib
import yaml
import logging

pytestmark = pytest.mark.usefixtures("register_subman")
TEST_CMD = ["uptime", "lsmod"]
TEST_FILE = ["/proc/cpuinfo", "/proc/meminfo", "/etc/yum.conf", "/etc/os-release"]
FILE_REDACTION_FILE = "/etc/insights-client/file-redaction.yaml"
CONTENT_REDACTION_FILE = "/etc/insights-client/file-content-redaction.yaml"


@pytest.mark.parametrize("not_removed_command", TEST_CMD)
def test_redaction_not_on_cmd(insights_client, not_removed_command):
    """
    Do not configure commands in /etc/insights-client/file-redaction.yaml,
    so related commands should exist in collection archive.
    """
    insights_client.register()
    sleep(5)
    assert insights_client.is_registered
    with contextlib.suppress(Exception):
        os.remove("/etc/insights-client/file-redaction.yaml")
        os.remove("/etc/insights-client/remove.conf")
    assert check_archive(insights_client, not_removed_command)


@pytest.mark.parametrize("removed_command", TEST_CMD)
def test_redaction_on_cmd(insights_client, removed_command):
    """
    Configure command redaction in /etc/insights-client/file-redaction.yaml,
    so related commands should not exist in collection archive.
    """
    try:
        configure_file_redaction("command", removed_command)
        insights_client.register()
        sleep(5)
        assert insights_client.is_registered
        assert not check_archive(insights_client, removed_command)
    finally:
        os.remove(FILE_REDACTION_FILE)


@pytest.mark.parametrize("not_removed_file", TEST_FILE)
def test_redaction_not_on_file(insights_client, not_removed_file):
    """
    Do not configure files in /etc/insights-client/file-redaction.yaml,
    so related files should exist in collection archive.
    """
    insights_client.register()
    sleep(5)
    assert insights_client.is_registered
    with contextlib.suppress(Exception):
        os.remove("/etc/insights-client/file-redaction.yaml")
        os.remove("/etc/insights-client/remove.conf")
    assert check_archive(insights_client, not_removed_file)


@pytest.mark.parametrize("removed_file", TEST_FILE)
def test_redaction_on_file(insights_client, removed_file):
    """
    Redact files in /etc/insights-client/file-redaction.yaml,
    so related files should not exist in collection archive.
    """
    try:
        configure_file_redaction("file", removed_file)
        insights_client.register()
        sleep(5)
        assert insights_client.is_registered
        assert not check_archive(insights_client, removed_file)
    finally:
        os.remove(FILE_REDACTION_FILE)


def test_redaction_on_pattern_hostname(insights_client, tmp_path):
    """
    Test if the satellite hostname is obfuscated
    Related to https://issues.redhat.com/browse/RHEL-2471

    """
    # Register system to insights
    insights_client.register()
    # sleep(5)
    # assert insights_client.is_registered

    # Record the current hostname
    with open("/etc/hostname", "r") as f:
        previous_hostname = f.read().strip()

    try:
        # Set a new hostname
        hostname_to_test = "insights-client-satellite"
        set_hostname(hostname_to_test)
        cmd = ["hostnamectl", "status"]
        output = subprocess.check_output(cmd, universal_newlines=True)
        assert hostname_to_test in output

        # redaction on hostname:
        configure_content_redaction(hostname_to_test)

        # check the collection, if redaction pattern is filtered out
        # collect data
        archive_result = insights_client.run("--no-upload")

        # extract the collected tar file
        m = re.search("^Archive saved at (.+)$", archive_result.stdout, re.MULTILINE)
        assert m
        archive_location = m.group(1)
        cmd = ["tar", "-vxzf", archive_location, "-C", tmp_path]
        subprocess.check_call(cmd)

        # the redaction data should not locate in the collected files
        archive_extract = os.path.basename(archive_location).split(".")[0]
        path_to_check = tmp_path / archive_extract
        cmd = ["grep", "-rnw", ".", "-e", hostname_to_test]
        # should not find the obfuscate pattern, the return code should not zero.
        ret = subprocess.run(cmd, cwd=path_to_check)
        assert ret.returncode == 1
    finally:
        # Recover the previous hostname for the system
        set_hostname(previous_hostname)
        # Remove all data redaction
        os.remove(CONTENT_REDACTION_FILE)


def configure_file_redaction(redaction_type, redaction_string):
    if redaction_type == "command":
        file_content = {"commands": [redaction_string]}
    elif redaction_type == "file":
        file_content = {"files": [redaction_string]}
    with open(FILE_REDACTION_FILE, "w") as f:
        yaml.dump(file_content, f, default_flow_style=False)
    os.chmod(FILE_REDACTION_FILE, 0o600)


def check_archive(insights_client, tested):
    archive_result = insights_client.run("--no-upload")
    m = re.search("^Archive saved at (.+)$", archive_result.stdout, re.MULTILINE)
    assert m
    archive_location = m.group(1)
    with tarfile.open(archive_location, "r:gz") as tar:
        check_tested = [
            w_file for w_file in tar.getmembers() if w_file.name.endswith(tested)
        ]
    logging.info(check_tested)
    return check_tested


def configure_content_redaction(pattern_string):
    file_content = {"patterns": {"regex": [pattern_string]}}
    with open(CONTENT_REDACTION_FILE, "w") as f:
        yaml.dump(file_content, f, default_flow_style=False)
    os.chmod(CONTENT_REDACTION_FILE, 0o600)


def set_hostname(hostname_to_set):
    cmd = ["hostnamectl", "set-hostname", hostname_to_set]
    subprocess.check_call(cmd)
