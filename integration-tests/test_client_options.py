"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: sst_csi_client_tools
:caseautomation: Automated
:upstream: Yes
"""

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
    :id: 18fc9438-8f2e-40f7-88b8-b51f36c9c396
    :title: Test set ansible host info
    :description:
        This test verifies that the --ansible-host option can be used
        to set the ansible host with a satellite-registered system
    :reference: https://issues.redhat.com/browse/RHEL-3826
    :tier: Tier 1
    :steps:
        1. Register insights-client
        2. Run insights-client with the --ansible-host=foo.example.com
            to update the host
        3. Verify the return code of the command is 0
    :expectedresults:
        1. Insights-client is registered
        2. The command completes successfully
        3. The return code is 0
    """
    # Register system against Satellite, and register insights through satellite
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    # Update ansible-host
    ret = insights_client.run("--ansible-host=foo.example.com", check=False)
    assert "Could not update Ansible hostname" not in ret.stdout
    assert ret.returncode == 0


def test_no_upload(insights_client):
    """
    :id: e55b7148-8d71-406d-a0d0-c1157a455cd5
    :title: Test no upload command
    :description:
        This test verifies that no traceback is returned when running --no-upload
        command and the archive is created and saved
    :reference:
    :tier: Tier 1
    :steps:
        1. Register insights-client
        2. List the archives in the cache directory before running --no-upload
        3. Run insights-client with --co-upload command to generate the archive
        4. List the archives in the cache directory after running --no-upload
    :expectedresults:
        1. Insights-client is registered
        2. A list of current archives is generated
        3. The archive is created and saved locally
        4. The number of archives should be greater confirming the new
            archive was created and saved
    """
    archive_saved = "Archive saved at"
    upload_message = "Successfully uploaded report"

    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    archive_file_before = glob.glob(f"{ARCHIVE_CACHE_DIRECTORY}/*.tar.gz")

    no_upload_output = insights_client.run("--no-upload")
    assert archive_saved in no_upload_output.stdout
    assert upload_message not in no_upload_output.stdout

    archive_file_after = glob.glob(f"{ARCHIVE_CACHE_DIRECTORY}/*.tar.gz")
    assert len(archive_file_after) > len(archive_file_before)


def test_group(insights_client, tmp_path):
    """
    :id: 29215bcc-1276-43cc-b87b-48d75f458426
    :title: Test group option
    :description:
        This test verifies that the --group option is functional, ensuring that the
        group specified is created and packed in the archive
    :reference:
    :tier: Tier 1
    :steps:
        1. Run insights-client in offline mode to generate archive
            with the --group option
        2. Open the generated archive
        3. Extract and verify the contents of the tags.json file to check
            if the group information is present
    :expectedresults:
        1. The archive is successfully generated with specified group
        2. The archive opens and its contents are accessible
        3. The tags.json file contains the group with the correct key, namespace
            and value
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
    """
    :id: 43dbe53c-c8ec-41f2-8f1f-2396f07272cb
    :title: Test support option
    :description:
        This test verifies that the --support option provides the expected
        information and generates a support log for Red Hat insights
    :reference:
    :tier: Tier 1
    :steps:
        1. Run insights-client with --support option
    :expectedresults:
        1. The command executes successfully, generating a support log
            with output specifying 'insights version', 'registration check',
            'last successful upload', 'connectivity tests', 'running command',
            'process output' and 'support information collected'
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
    """
    :id: 2ca44ace-efe6-471c-8a4d-f24c9a913233
    :title: Test validate with no network call
    :description:
        This test verifies that the --validate option does not attempt to
        connect to any network service
    :reference: https://bugzilla.redhat.com/show_bug.cgi?id=2009864
    :tier: Tier 1
    :steps:
        1. Create an empty tags.yaml in /etc/insights-client/
        2. Modify the configuration to prevent any connection attempts to
            external network services
        3. Run insights-client with the --validate option
        4. Verify that no metrics data is included in the output and
            remove the tags.yaml file
    :expectedresults:
        1. The tags.yaml is created
        2. The configuration is updated successfully
        3. The command executes and the output confirms that the tags.yaml
            file was loaded without attempting any network connections
        4. The output does not contain any metrics entries and then is removed
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
    """
    :id: 05803f81-ebd6-4d58-9061-4d0403d8d9fc
    :title: Test check-in in offline mode
    :description:
        This test verifies that running the --checkin command in offline
        mode logs an appropriate message and exits with a failure code
    :reference:
    :tier: Tier 1
    :steps:
        1. Register insights-client
        2. Run insights-client with --offline and --checkin options
    :expectedresults:
        1. Insights-client is registered successfully
        2. The command fails with a return code of 1 and output includes
            message 'ERROR: Cannot check-in in offline mode.'
    """
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)
    checkin_result = insights_client.run("--offline", "--checkin", check=False)
    assert checkin_result.returncode == 1
    assert "ERROR: Cannot check-in in offline mode." in checkin_result.stderr


def test_client_diagnosis(insights_client):
    """
    :id: 7659051f-0e87-4fd7-bc95-0152077fe67e
    :title: test diagnosis option
    :description:
        This test verifies that on a registered system, the --diagnosis
        option retrieves the correct diagnostic information
    :reference:
    :tier: Tier 1
    :steps:
        1. Run the --diagnosis option on unregistered system
        2. Register insights-client
        3. Run the --diagnosis option on registered system
        4. Verify the machine id in the diagnostic data matches the
            system's machine id
    :expectedresults:
        1. The command fails with an error message indicating that diagnosis
            data cannot be retrieved (404)
        2. The client is registered
        3. The command retrieves diagnostic data and the output contains
            machine id
        4. The machine ID in the diagnostic data matches the system's machine id
    """
    # Running diagnosis on unregistered system returns appropriate error message
    diagnosis_result = insights_client.run("--diagnosis", check=False)
    assert "Unable to get diagnosis data: 404" in diagnosis_result.stdout
    # Running diagnosis on registered system
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)
    with open("/etc/insights-client/machine-id", "r") as f:
        machine_id = f.read()
    diagnosis_result = insights_client.run("--diagnosis")
    diagnosis_data = json.loads(diagnosis_result.stdout)
    # verify that diagnosis contains correct machine id
    assert diagnosis_data["insights_id"] == machine_id


def test_check_show_results(insights_client):
    """
    :id: 82571026-af14-464c-b9ff-5c03ecfe77c9
    :title: Test check results and show results
    :description:
        This test verifies that when checking results from the Advisor (--check-results)
        and displaying them (--show-results), a remediation is advised
    :reference:
    :tier: Tier 1
    :steps:
        1. Register insights-client
        2. Change permissions of /etc/ssh/sshd_config file to introduce a vulnerability
        3. Run insights-client with --check-results option
        4. Run the insights-client with --show-results option
    :expectedresults:
        1. The client is registered
        2. The permissions of the file are set to 0o777
        3. The command runs successfully and checks for vulnerabilities
            retrieving the results
        4. The output includes a remediation for the OpenSSH config permission issue
    """
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    try:
        os.chmod("/etc/ssh/sshd_config", 0o777)

        insights_client.run()

        insights_client.run("--check-results")
        show_results = insights_client.run("--show-results")

        assert (
            "hardening_ssh_config_perms|OPENSSH_HARDENING_CONFIG_PERMS"
            in show_results.stdout
        )
        assert "Decreased security: OpenSSH config permissions" in show_results.stdout
        assert (
            "examine the following detected issues in OpenSSH settings:"
            in show_results.stdout
        )
        assert "OPENSSH_HARDENING_CONFIG_PERMS" in show_results.stdout
    finally:
        os.chmod("/etc/ssh/sshd_config", 0o600)
