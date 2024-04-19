import json
import os
import tarfile
import pytest
import conftest
import glob

pytestmark = pytest.mark.usefixtures("register_subman")

ARCHIVE_CACHE_DIRECTORY = "/var/cache/insights-client"


def test_set_ansible_host_info(insights_client):
    """
    Test if the ansible-host can be set with satellite
    Related to https://issues.redhat.com/browse/RHEL-3826
    """
    # Register system against Satellite, and register insights through satellite
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    # Update ansible-host
    ret = insights_client.run("--ansible-host=foo.example.com", check=False)
    assert "Could not update Ansible hostname" not in ret.stdout
    assert ret.returncode == 0


def test_no_upload(insights_client):
    """Verify no traceback is returned when running '--no-upload' command
    and the archive is created and saved on the system
    """
    archive_saved = "Archive saved at"
    upload_message = "Successfully uploaded report"

    insights_client.register()

    archive_file_before = glob.glob(f"{ARCHIVE_CACHE_DIRECTORY}/*.tar.gz")

    no_upload_output = insights_client.run("--no-upload")
    assert archive_saved in no_upload_output.stdout
    assert upload_message not in no_upload_output.stdout

    archive_file_after = glob.glob(f"{ARCHIVE_CACHE_DIRECTORY}/*.tar.gz")
    assert len(archive_file_after) > len(archive_file_before)


def test_group(insights_client, tmp_path):
    """Test --group option
    This test generates an archive in offline mode and verifies if the group
    specified in --group was created and packed
    """

    group_name = "testing-group"
    archive_name = "archive.tar.gz"
    archive_location = tmp_path / archive_name

    # Running insights-client in offline mode to generate archive
    insights_client.run(
        "--offline", f"--group={group_name}", f"--output-file={archive_location}"
    )

    with tarfile.open(archive_location, "r") as tar:
        dir_name = tar.getnames()[0]
        for m in tar.getmembers():
            if m.name == f"{dir_name}/tags.json":
                tag_file = tar.extractfile(m)
                tag_file_content = json.load(tag_file)
                break

    assert len(tag_file_content) == 1

    tag = tag_file_content[0]
    assert tag["key"] == "group"
    assert tag["namespace"] == "insights-client"
    assert tag["value"] == group_name


def test_support(insights_client):
    """Test if --support option is giving expected information in output
    and generates a support logfile for Red Hat Insights.
    """
    support_result = insights_client.run("--support")

    assert "Insights version:" in support_result.stdout
    assert "Registration check:" in support_result.stdout
    assert "Last successful upload was" in support_result.stdout
    assert "Connectivity tests" in support_result.stdout
    assert "Running command:" in support_result.stdout
    assert "Process output:" in support_result.stdout
    assert "Support information collected in" in support_result.stdout


def test_client_validate_no_network_call(insights_client):
    """Verify that '--validate' option will not try to connect to any network service.

    Ref : https://bugzilla.redhat.com/show_bug.cgi?id=2009864
    """
    try:
        # '/etc/insights-client/tags.yaml' file exists with any content
        tags_filename = "/etc/insights-client/tags.yaml"
        with open(tags_filename, "w"):
            pass

        # modifying conf so that any attempt to connect to any
        # network service would fail
        insights_client.config.base_url = "non-existent-url.redhat.com:442/r/insights"
        insights_client.config.auto_config = False
        insights_client.config.auto_update = False

        validate_result = insights_client.run("--validate")

        # validating tags.yaml is loaded and no metric data in output
        assert (
            "/etc/insights-client/tags.yaml loaded successfully"
            in validate_result.stdout
        )
        assert "metrics Metrics:" not in validate_result.stdout
    finally:
        # Remove tags file at the end of test to leave system in clean state
        os.remove(tags_filename)


def test_client_checkin_offline(insights_client):
    """This test verifies that running --checkin with --offline, a friendly message is
    logged, and it exists with a failure code
    """
    insights_client.register()
    checkin_result = insights_client.run("--offline", "--checkin", check=False)
    assert checkin_result.returncode == 1
    assert "ERROR: Cannot check-in in offline mode." in checkin_result.stderr
