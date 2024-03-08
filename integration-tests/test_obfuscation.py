import pytest
import subprocess
import os
import yaml
from time import sleep
import re

pytestmark = pytest.mark.usefixtures("register_subman")
CONTENT_REDACTION_FILE = "/etc/insights-client/file-content-redaction.yaml"


def test_obfuscation(insights_client, tmp_path):
    """
    Test if the satellite hostname is obfuscated
    Related to https://issues.redhat.com/browse/RHEL-2471

    """
    # Register system to insights
    insights_client.register()
    sleep(5)
    assert insights_client.is_registered

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
        data_redaction(hostname_to_test)

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


def set_hostname(hostname_to_set):
    cmd = ["hostnamectl", "set-hostname", hostname_to_set]
    subprocess.check_call(cmd)


def data_redaction(pattern_string):
    file_content = {"patterns": {"regex": [pattern_string]}}
    with open(CONTENT_REDACTION_FILE, "w") as f:
        yaml.dump(file_content, f, default_flow_style=False)
    os.chmod(CONTENT_REDACTION_FILE, 0o600)
