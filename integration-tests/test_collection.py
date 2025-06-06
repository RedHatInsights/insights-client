"""
:component: insights-client
:requirement: RHSS-291297
:polarion-project-id: RHELSS
:polarion-include-skipped: false
:polarion-lookup-method: id
:poolteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import contextlib
import os
import tarfile
import json
import pytest
import conftest
import uuid


@pytest.mark.tier1
def test_output_file_valid_parameters(insights_client, tmp_path):
    """
    :id: 011e38c7-c6dc-4c17-add4-d67f0775f5cd
    :title: Test --output-file with valid parameters
    :description:
        This test verifies that the --output-file option correctly
        creates a new archive file when provided with a valid path
    :tags: Tier 1
    :steps:
        1. Define the archive name path
        2. Run insights-client in an offline mode with --output-file
            pointing to the archive name
        3. Verify that a new archive file is created
        4. Verify that the command output confirms the collected
            data was copied to the new archive
    :expectedresults:
        1. The archive name path is set correctly
        2. The insights-client runs successfully with the specified output file path
        3. A new archive file are created at the specified location
        4. The command output confirms that the collected data was copied to the new
            archive
    """
    archive_name = tmp_path / "archive"

    # Running insights-client in offline mode to generate archive
    cmd_result = insights_client.run(f"--output-file={archive_name}")
    assert os.path.isfile(f"{archive_name}.tar.gz")
    assert f"Collected data copied to {archive_name}.tar.gz" in cmd_result.stdout


@pytest.mark.tier1
def test_output_file_non_existing_path(insights_client):
    """
    :id: 003faa12-8daa-417b-83bb-71aaa80209b6
    :title: Test --output-file with non-existing path
    :description:
        Checks that the --output-file option fails with an appropriate error
        message when provided with a non-existent path
    :tags: Tier 1
    :steps:
        1. Define an archive file path in a non-existing directory
            and define the parent directory path
        2. Run insights-client with the --output-file option pointing
            to an non-existing path
        3. Verify that the command output fails with a return code of 1
        4. Verify that the error message indicates the parent directory
            does not exist
    :expectedresults:
        1. The archive path is set to a non-existent directory
            and the parent directory path is correctly derived
        2. The insights-client runs with the specified output file path
        3. The command returns code of 1
        4. The error message contains the expected message
    """
    archive_location = "/not-existing-dir/archive_file.tar.gz"
    parent_dir = os.path.dirname(archive_location)
    cmd_result = insights_client.run(f"--output-file={archive_location}", check=False)
    assert cmd_result.returncode == 1
    assert (
        f"Cannot write to {archive_location}. Parent"
        f" directory {parent_dir} does not exist." in cmd_result.stderr
    )


@pytest.mark.tier1
def test_output_dir_without_specifying_a_path(insights_client):
    """
    :id: 63eb1ba0-b9dd-4185-b422-18325c12b503
    :title: Test --output-dir without specifying a path
    :description:
        Verifies that the --output-dir option fails with an appropriate
        error message when no path is specified
    :tags: Tier 1
    :steps:
        1. Run insights-client with an empty --output-file option
        2. Verify that the command fails with a return code of 1
        3. Verify that the error message indicates that --output-file cannot be empty
    :expectedresults:
        1. The insights-client runs with an empty option
        2. The command fails with a return code of 1
        3. The error message is as expected
    """
    cmd_result = insights_client.run("--output-file=", check=False)
    assert cmd_result.returncode == 1
    assert "ERROR: --output-file cannot be empty" in cmd_result.stderr


@pytest.mark.tier1
def test_output_specifying_both_dir_and_file(insights_client, tmp_path):
    """
    :id: a572654d-904c-410e-ba00-f7b63f910e53
    :title: Test --output-file specifying both directory and file
    :description:
        Verifies that specifying both output file and output directory
        option together fails with an appropriate error message
    :tags: Tier 1
    :steps:
        1. Define both output file and directory paths
        2. Run insights-client with --output-file and --output-dir
        3. Verify the command fails with an error code of 1
        4. Verify the error message says they can't be used together
    :expectedresults:
        1. the output file and directory paths are set correctly
        2. The insights-client runs with specified options
        3. The command fails with a return code of 1
        4. The error message is as expected
    """
    # Parent directory does not exist
    output_file = tmp_path / "output_file.tar.gz"
    output_dir = tmp_path
    cmd_result = insights_client.run(
        f"--output-file={output_file}", f"--output-dir={output_dir}", check=False
    )
    assert cmd_result.returncode == 1
    assert "Specify only one: --output-dir or --output-file." in cmd_result.stderr


@pytest.mark.tier1
def test_output_file_with_relative_path(insights_client):
    """
    :id: e1236f11-46c3-452c-81b8-3c61506e1841
    :title: Test --output-file with relative path
    :description:
        Verifies that using a relative path that points to a directory
        with the --output-file option fails with an appropriate error message
    :tags: Tier 1
    :steps:
        1. Define a relative path pointing to a directory
        2. Run insights-client with the --output file option pointing to
            this relative path
        3. Verify that the command fails with a return code of 1
        4. Verify the error message says that --output
            cannot be used with a directory
    :expectedresults:
        1. The relative path is correctly
        2. The insights-client runs with the specified option
        3. The command fails with an exit code of 1
        4. The error message is as expected
    """
    relative_path = os.path.realpath("")
    cmd_result = insights_client.run(f"--output-file={relative_path}", check=False)
    assert cmd_result.returncode == 1
    assert f"{relative_path} is a directory." in cmd_result.stderr


@pytest.mark.tier1
def test_output_dir_with_not_empty_directory(insights_client):
    """
    :id: 30384d37-92b4-4196-8423-0355b0cbef30
    :title: Test --output-dir with non-empty directory
    :description:
        Verify that when the --output-dir option is used with an existing
        non-empty directory, the command fails with an appropriate error message
    :tags: Tier 1
    :steps:
        1. Define a path to an existing non-empty directory
        2. Run insights-client with --output-dir option specified
        3. Verify the command fails with a return code of 1
        4. Verify the error message is as expected
    :expectedresults:
        1. The path to the non-empty directory is set correctly
        3. The insights-client is run
        4. The command fails with a return code of 1
        5. The error message is as expected
    """
    relative_path = os.path.realpath("")
    cmd_result = insights_client.run(f"--output-dir={relative_path}", check=False)
    assert cmd_result.returncode == 1
    assert (
        f"Directory {relative_path} already exists and is not empty."
        in cmd_result.stderr
    )


@pytest.mark.tier1
def test_output_dir_creates_archive_for_directory(insights_client, tmp_path):
    """
    :id: 6a966179-3b61-4a74-8af4-68fa0c2c237e
    :title: Test --output-file creates archive for directory
    :description:
        Checks that when the --output-file option is used with a path
        that is an existing directory, the insights-client correctly generates
        an archive with the directory name appended with .tar.gz
    :tags: Tier 1
    :steps:
        1. Define a directory path
        2. Run insights-client with the --output-file option pointing to that directory
        3. Verify that the command creates an archive file with the directory name
            and extension
        4. Clean up by removing the generated archive file
    :expectedresults:
        1. The directory is set correctly
        2. The insights-client runs with the specified dir path
        3. An archive file with the directory name is created
        4. The generated archive file is successfully removed
    """
    directory = "/tmp/directory/"
    try:
        cmd_result = insights_client.run(f"--output-file={directory}", check=False)
        assert os.path.abspath(directory[0:-1] + ".tar.gz") in cmd_result.stdout
    finally:
        os.remove(os.path.abspath(directory[0:-1] + ".tar.gz"))


@pytest.mark.tier1
def test_output_file_already_exists(insights_client, tmp_path):
    """
    :id: 36456352-da31-4633-872a-061c2045176a
    :title: Test --output-file already exists
    :description:
        Verify that when the --output-file option is used with a path
        that points to an existing archive file, the command fails with an
        appropriate error message
    :tags: Tier 1
    :steps:
        1. Create an archive file at a specified location
        2. Run insights-client with the --output-file option to this existing archive
        3. Verify the command fails with a return code of 1
        4. Verify that the error message indicates that the file already exists
    :expectedresults:
        1. The archive file is created at the specified location
        2. The insights-client is run with the specified output file path
        3. The command fails with a return code of 1
        4. The error message indicates that the file already exists
    """
    # File should already exist
    output_file = tmp_path / "output_file.tar.gz"
    with contextlib.suppress(Exception):
        with tarfile.open(output_file, "w:gz"):
            pass

    cmd_result = insights_client.run(f"--output-file={output_file}", check=False)
    assert cmd_result.returncode == 1
    assert f"ERROR: File {output_file} already exists." in cmd_result.stderr


@pytest.mark.usefixtures("register_subman")
@pytest.mark.tier2
def test_cmd_timeout(insights_client):
    """
    :id: 0a55318c-28e0-4ca7-bdbf-3eb8c0d689ea
    :title: Test cmd_timeout configuration
    :description:
        Verify that the cmd_timeout configuration correctly limits the
        execution time of commands, killing them if they exceed said limit
    :tags: Tier 2
    :steps:
        1. Register insights-client
        2. Set the cmd_timeout option to 10 seconds
        3. Run insights-client with a command that would take longer than the
            the timeout limit
        4. Verify the command is terminated after 10 seconds
        5. Verify that the output includes the expected message
    :expectedresults:
        1. The insights-client is registered
        2. The cmd_timeout option is set to 10 seconds
        3. The command is run with the specified timeout
        4. The command is terminated after 10 seconds
        5. The output contains "Executing: [['timeout', '-s', '9', '10'"
    """
    cmd_output_message = "Executing: [['timeout', '-s', '9', '10'"

    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    insights_client.config.cmd_timeout = 10
    insights_client.config.save()

    timeout_output = insights_client.run("--verbose", check=False)
    assert cmd_output_message in timeout_output.stdout


@pytest.mark.usefixtures("register_subman")
@pytest.mark.tier2
def test_branch_info(insights_client, test_config, subman, tmp_path):
    """
    :id: 22c7063c-e09d-4fdf-80ea-864a7027d2ee
    :title: Test branch_info file includes all required information
    :description:
        Verify that the branch_info file generated by the insights-client
        contains all necessary information for identifying the host when connected
        via Satellite
    :reference:
        https://docs.google.com/document/d/193mN5aBwxtzpP4U-vnL3yVawPxiG20n0zkzDYsam-eU/edit
    :tags: Tier 2
    :steps:
        1. Run insights-client with --output-dir
        2. Inspect the branch_info file to verify it contains correct values
    :expectedresults:
        1. The branch_info file is generated
        2. The branch_info includes correct values
    """
    insights_client.run("--output-dir", tmp_path.absolute())
    with (tmp_path / "data/branch_info").open("r") as file:
        data = json.load(file)

    if "satellite" in test_config.environment:
        assert data["product"]["type"] == "Satellite"
        assert isinstance(uuid.UUID(data["remote_branch"]), uuid.UUID)
        assert uuid.UUID(data["remote_leaf"]) == subman.uuid
    else:
        assert data["remote_branch"] == -1, "Incorrect remote_branch value"
        assert data["remote_leaf"] == -1, "Incorrect remote_leaf value"


@pytest.mark.tier1
def test_archive_structure(insights_client, tmp_path):
    """
    :id: 7a78cf8f-ed32-4011-8d15-787231f867c9
    :title: Test archive structure
    :description:
        Verify that the generated archive from insights-client has the
        correct directory structure and contains all the necessary directories
        and subdirectories
    :tags: Tier 1
    :steps:
        1. Run insights-client with --output-dir
        2. Verify that all required directories are present in the archive
        3. Verify that all required subdirectories are present under the
            data directory
    :expectedresults:
        1. The archive is saved uncompressed into a directory
        2. Expected directories are present
        3. Expected subdirectories are present
    """
    archive_content = [
        "data",
        "meta_data",
    ]

    archive_data_content = [
        "branch_info",
        "version_info",
        "etc",
        "insights_commands",
        "proc",
        "sys",
        "usr",
    ]

    insights_client.run("--output-dir", tmp_path.absolute())
    extracted_dirs_files = os.listdir(tmp_path)  # type: list[str]
    missing_dirs = [f for f in archive_content if f not in extracted_dirs_files]
    assert not missing_dirs, f"Missing directories {missing_dirs}"

    data_subdirs = os.listdir(tmp_path / "data")  # type: list[str]
    missing_subdirs = [f for f in archive_data_content if f not in data_subdirs]
    assert not missing_subdirs, f"Missing subdirectory {missing_subdirs}"
