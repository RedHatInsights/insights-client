import contextlib
import glob
import os
import subprocess
import pytest
import conftest

"""
:requirement: RHSS-291297
:subsystemteam: sst_csi_client_tools
:caseautomation: Automated
:upstream: Yes
"""


@pytest.mark.usefixtures("register_subman")
def test_client_files_permission(insights_client):
    """
    :title: Verify Client Files Permission
    :description: Verify that the permission for the last upload file
    '/etc/insights-client'/.lastupload is set to 0644
    :tier: Tier 0
    :steps:
        1. Remove /etc/insights-client/.lastupload if it exists
        2. Register insights-client
        3. Verify the file permissions
    :expected results:
        1. The file /etc/insights-client/.lastupload does not exist
        2. The insights-client registers successfully
        3. The permission of /etc/insights-client/.lastupload is set to 0644
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
    :title: Verify mandatory files for RPM
    :description: Verify the existence of mandatory files for the insights-client RPM
    :tier: Tier 0
    :steps:
        1. List all files in the insights-client RPM package
        2. Check if each mandatory file existsin the package
    :expected results:
        1. A list of files is generated
        2. All of the mandatory files are present in the RPM
    """
    assert (
        filename in rpm_ql_insights_client
    ), f"{filename} is not in insights-client package"


@pytest.mark.usefixtures("register_subman")
def test_client_logfiles_mask(insights_client):
    """
    :title: Verify Client logfiles Mask
    :description: Verify that the log files in
    /var/log/insights-client have the correct mode 0600
    :tier: Tier 0
    :steps:
        1. Register the insights-client to generate log files
        2. Check the file permission of each log file generated
    :expected results:
        1. Insights-client is registered and log files are generated
        2. The file permissions for all log files are 0600
    """
    # It is necessary to perform some command using insights-client
    # to populate logs
    insights_client.register()
    logfiles = glob.glob("/var/log/insights-client/*.log*")
    for logfile in logfiles:
        assert oct(os.stat(logfile).st_mode & 0o777) == "0o600"


def test_client_logdir_permissions():
    """
    :title: Verify log directory permissions
    :description: Verify that the permissions on the directory
    /var/log/insights-client are set to 0700
    :tier: Tier 0
    :steps: Check the directory permissions of /var/log/insights-client
    :expected results: The directory permissions are set to 0700
    """
    logdir_name = "/var/log/insights-client"
    assert oct(os.stat(logdir_name).st_mode & 0o777) == "0o700"


@pytest.mark.usefixtures("register_subman")
def test_verify_logrotate_feature(insights_client):
    """
    :title: Verify Logrotate feature
    :description: Verify that the logrotate works properly for insights-client
    :tier: Tier 1
    :steps:
        1. Ensure the logrotate configuration file exists
        2. Register insights-client and perform pazload operations
        3. Run the logrotate command
        4. Verify that 2 new log files were created
        5. Verify the size of insights-client.log
        6. Verify the size of insights-client-payload.log
    :expected results:
        1. The logrotate config file exists
        2. The insights-client registers successfully and logs are populated
        3. The logrotate command is executed successfully
        4. Two new log files were created
        5. The size is 0B
        6. The size is 0B
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
    :title: Verify insights-client details file exists
    :description: Verify that the file /var/lib/insights/insights-client.json exists
    :tier: Tier 0
    :steps:
        1. Register the insights-client
        2. Delete /var/lib/insights/insights-client.json if it exists
        3. run the --check-results command
        4. Verify the existence of /var/lib/insights/insights-client.json
    :expected results:
        1. Insights-client is registrated
        2. The file /var/lib/insights/insights-client.json does not exists
        3. The --check-results command is executed successfully
        4. The file /var/lib/insights/insights-client.json exists
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
    :title: Verify insights directory files
    :description: Verify that the /var/lib/insights directory has the expected content
    :tier: Tier 0
    :steps:
        1. Register the insights-client
        2. Check the content of /var/lib/insights directory
        3. Verify specific files exists
    :expected results:
        1. Insights-client is registered
        2. The list of contents of /var/lib/insights directory is created
        3. All specified files are present
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
