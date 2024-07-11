import contextlib
import glob
import os
import subprocess
import pytest
import conftest


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
    assert conftest.loop_until(lambda: insights_client.is_registered)
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
        1 - Perform register and payload operation to ensure both
            insights-client.log and insights-client-payload.log files have logs
        2 - Rotate logs by running logrotate command on CLI for insights-client
        3 - Verify insights-client.log and insights-client-payload.log size is 0B
        4 - Verify rotated files are created in log dir by comparing number of log files
    """

    logrotate_conf_file_path = "/etc/logrotate.d/insights-client"
    logdir = "/var/log/insights-client/"
    logfile_insights = f"{logdir}/insights-client.log"
    logfile_payload = f"{logdir}/insights-client-payload.log"

    assert os.path.exists(logrotate_conf_file_path), "logrotate is not configured"
    """
     It is necessary to perform some command using insights-client
     to populate logs.
     Save the archive, to be used while register operation using --keep-archive.
     for example-
     [root@test ~]# insights-client --register --keep-archive
     Automatic scheduling for Insights has been enabled.
     Starting to collect Insights data for test
     Writing RHSM facts to /etc/rhsm/facts/insights-client.facts ...
     Uploading Insights data.
     Successfully uploaded report for test.
     View the Red Hat Insights console at https://console.redhat.com/insights/
     Copying archive from /var/tmp/insights-client-qxl3vdqy/insights-test-date.tar.gz
     to /var/cache/insights-client/insights-test-date.tar.gz
     Insights archive retained in /var/cache/insights-client/insights-test-date.tar.gz
    """
    reg_result = insights_client.run("--register", "--keep-archive")
    assert conftest.loop_until(lambda: insights_client.is_registered)

    archive_name = reg_result.stdout.split()[-1]
    insights_client.run(
        f"--payload={archive_name}",
        "--content-type=gz",
    )
    number_of_log_files = len(os.listdir(logdir))  # count of files before rotation

    subprocess.check_call(["logrotate", "-vf", logrotate_conf_file_path])
    assert os.path.getsize(logfile_insights) == 0
    assert os.path.getsize(logfile_payload) == 0
    number_of_files_after_logrotate = len(os.listdir(logdir))
    assert number_of_files_after_logrotate == (number_of_log_files + 2)


@pytest.mark.usefixtures("register_subman")
def test_insights_details_file_exists(insights_client):
    """
    This test verifies that /var/lib/insights/insights-details.json exists
    when --check-results is called
    """
    output_file = "/var/lib/insights/insights-details.json"
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    # Deleting file manually
    with contextlib.suppress(FileNotFoundError):
        os.remove(output_file)
    insights_client.run("--check-results")
    # Verify that insights-details.json gets re generated
    assert os.path.isfile(output_file)


@pytest.mark.usefixtures("register_subman")
def test_insights_directory_files(insights_client):
    """
    Test that /var/lib/insights have content available
    """
    directory = "/var/lib/insights"
    registered_contents = [
        "last_stable.egg",
        "last_stable.egg.asc",
    ]

    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    dir_content_registered = [
        entry.name for entry in os.scandir(directory) if entry.is_file()
    ]

    for item in registered_contents:
        assert item in dir_content_registered, f"File '{item}' not found in directory."
