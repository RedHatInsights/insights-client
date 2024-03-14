import contextlib
import glob
import os
import subprocess
import pytest


@pytest.mark.usefixtures("register_subman")
def test_client_files_permission(insights_client):
    """Verify that permission for lastupload file is 0644:
     file /etc/insights-client/.lastupload
    Ref: https://bugzilla.redhat.com/show_bug.cgi?id=1924990
    """
    file_last_upload = "/etc/insights-client/.lastupload"
    with contextlib.suppress(FileNotFoundError):
        os.remove(file_last_upload)  # performing a cleanup before test
    insights_client.register()
    assert insights_client.is_registered
    assert oct(os.stat(file_last_upload).st_mode & 0o777) == "0o644"


@pytest.fixture()
def rpm_ql_insights_client():
    cmd = ["rpm", "-ql", "insights-client"]
    list_file = subprocess.check_output(cmd, universal_newlines=True)
    return list_file.split("\n")


@pytest.mark.parametrize(
    "filename",
    [
        "/etc/insights-client/insights-client.motd",
        "/etc/insights-client/insights-client.conf",
        "/usr/lib/systemd/system/insights-client-boot.service",
        "/usr/lib/systemd/system/insights-client-results.path",
        "/usr/lib/systemd/system/insights-client-results.service",
        "/usr/lib/systemd/system/insights-client.service",
        "/usr/lib/systemd/system/insights-client.timer",
        "/usr/share/doc/insights-client/file-content-redaction.yaml.example",
        "/usr/share/doc/insights-client/file-redaction.yaml.example",
        "/usr/share/man/man5/insights-client.conf.5.gz",
        "/usr/share/man/man8/insights-client.8.gz",
        "/etc/logrotate.d/insights-client",
    ],
)
def test_client_rpm_mandatory_files(filename, rpm_ql_insights_client):
    """
    Verify the existence of mandatory files for insights-client rpm
    """
    assert (
        filename in rpm_ql_insights_client
    ), f"{filename} is not in insights-client package"


@pytest.mark.usefixtures("register_subman")
def test_client_logfiles_mask(insights_client):
    """Verify that files in /var/log/insights-client have the right mode: 0600

    Ref: https://bugzilla.redhat.com/show_bug.cgi?id=1955724
    """
    # It is necessary to perform some command using insights-client
    # to populate logs
    insights_client.register()
    logfiles = glob.glob("/var/log/insights-client/*.log*")
    for logfile in logfiles:
        assert oct(os.stat(logfile).st_mode & 0o777) == "0o600"


def test_client_logdir_permissions():
    """Verify that permissions on directory /var/log/insights-client
    have the right mode: 0700
    """
    logdir_name = "/var/log/insights-client"
    assert oct(os.stat(logdir_name).st_mode & 0o777) == "0o700"


@pytest.mark.usefixtures("register_subman")
def test_verify_logrotate_feature(insights_client):
    """
    Verify that the standard logrotate works for insights-client
    Ref : https://bugzilla.redhat.com/show_bug.cgi?id=1940267

    Test Steps:
        1-Count the number of log file in beginning
        2-Rotate logs by running logrotate command on CLI for insights-client
        3-Verify that log is rotated and new log file is created
    """

    logrotate_conf_file_path = "/etc/logrotate.d/insights-client"
    logdir = "/var/log/insights-client/"
    assert os.path.exists(logrotate_conf_file_path), "logrotate is not configured"
    # It is necessary to perform some command using insights-client
    # to populate logs
    insights_client.register()
    number_of_log_files = len(os.listdir(logdir))
    subprocess.check_call(["logrotate", "-vf", logrotate_conf_file_path])
    number_of_files_after_logrotate = len(os.listdir(logdir))
    assert number_of_files_after_logrotate == (number_of_log_files + 1)
