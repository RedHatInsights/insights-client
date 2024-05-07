import contextlib
import os
import tarfile
import glob
import json
import pytest

ARCHIVE_CACHE_DIRECTORY = "/var/cache/insights-client"


def test_output_file_valid_parameters(insights_client, tmp_path):
    """Test --output-file (with valid parameters)
    Test --output-file option pointing to:
        - a non-existing file (so a new one should be created properly)
    """
    archive_name = tmp_path / "archive"

    # Running insights-client in offline mode to generate archive
    cmd_result = insights_client.run(f"--output-file={archive_name}")
    assert os.path.isfile(f"{archive_name}.tar.gz")
    assert f"Collected data copied to {archive_name}.tar.gz" in cmd_result.stdout


def test_output_file_non_existing_path(insights_client):
    """Test --output-file (with invalid parameters)
    Test --output-file option pointing to:
        - not existing path (parent directory doesn't exist)
    """
    archive_location = "/not-existing-dir/archive_file.tar.gz"
    parent_dir = os.path.dirname(archive_location)
    cmd_result = insights_client.run(f"--output-file={archive_location}", check=False)
    assert cmd_result.returncode == 1
    assert (
        f"Cannot write to {archive_location}. Parent"
        f" directory {parent_dir} does not exist." in cmd_result.stderr
    )


def test_output_dir_without_specifying_a_path(insights_client):
    """Test --output-dir (without specifying path)"""
    cmd_result = insights_client.run("--output-file=", check=False)
    assert cmd_result.returncode == 1
    assert "ERROR: --output-file cannot be empty" in cmd_result.stderr


def test_output_specifying_both_dir_and_file(insights_client, tmp_path):
    """Test both --output-file and --output-dir (with valid parameters) at once.
    This should fail with error message suggesting to specify only one at a time.
    """
    # Parent directory does not exist
    output_file = tmp_path / "output_file.tar.gz"
    output_dir = tmp_path
    cmd_result = insights_client.run(
        f"--output-file={output_file}", f"--output-dir={output_dir}", check=False
    )
    assert cmd_result.returncode == 1
    assert "Specify only one: --output-dir or --output-file." in cmd_result.stderr


def test_output_file_with_relative_path(insights_client):
    """Test --output-file (with relative path)
    Test --output-file option pointing to:
        - relative path (so test will indicate path is already a directory)
    """
    relative_path = os.path.realpath("")
    cmd_result = insights_client.run(f"--output-file={relative_path}", check=False)
    assert cmd_result.returncode == 1
    assert f"{relative_path} is a directory." in cmd_result.stderr


def test_output_dir_with_not_empty_directory(insights_client):
    """Test --output-dir (with not empty directory)
    Test --output-dir option pointing to:
        - execution path (just to indicate a not empty dir, so test will indicate
          that dir already exists and is not empty)
    """
    relative_path = os.path.realpath("")
    cmd_result = insights_client.run(f"--output-dir={relative_path}", check=False)
    assert cmd_result.returncode == 1
    assert (
        f"Directory {relative_path} already exists and is not empty."
        in cmd_result.stderr
    )


def test_output_dir_creates_archive_for_directory(insights_client, tmp_path):
    """Test --output-file (indicating a directory, not a file)
    Test --output-file option pointing to:
        - existing directory (archive named should be generated combining
        the name of directory+'.tar.gz')
    """
    directory = "/tmp/directory/"
    try:
        cmd_result = insights_client.run(f"--output-file={directory}", check=False)
        assert os.path.abspath(directory[0:-1] + ".tar.gz") in cmd_result.stdout
    finally:
        os.remove(os.path.abspath(directory[0:-1] + ".tar.gz"))


def test_output_file_already_exists(insights_client, tmp_path):
    """Test --output-file (already existing archive)
    Test --output-file option pointing to:
        - already existing archive
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
def test_cmd_timeout(insights_client):
    """
    Test cmd_timeout config option
    Client executes all commands with timeout. If the command doesn't finish within
    a specified amount of seconds, it is killed.
    Test that setting a custom amount of seconds to cmd_timeout config option works.
    """
    cmd_output_message = "Executing: [['timeout', '-s', '9', '10'"

    insights_client.register()

    insights_client.config.cmd_timeout = 10
    insights_client.config.save()

    timeout_output = insights_client.run("--verbose", check=False)
    assert cmd_output_message in timeout_output.stdout


@pytest.mark.usefixtures("register_subman")
def test_branch_info(insights_client):
    """
    Test that branch_info includes all required information
    branch_info is used to identify the host when it is connectec via Satellite.
    It uses branch_id and leaf_id to identify
    """
    insights_client.register()
    insights_client.run("--no-upload")

    list_of_files = glob.glob(f"{ARCHIVE_CACHE_DIRECTORY}/*.tar.gz")
    latest_file = max(list_of_files, key=os.path.getctime)

    with tarfile.open(latest_file, "r:gz") as tar:
        tar.extractall(path="/var/cache/insights-client/", filter="data")
        directory_name = latest_file.replace(".tar.gz", "")

    branch_info_path = os.path.join(directory_name, "branch_info")
    with open(branch_info_path, "r") as file:
        data = json.load(file)
        assert data["remote_branch"] == -1, "Incorrect remote_branch value"
        assert data["remote_leaf"] == -1, "Incorrect remote_leaf value"


@pytest.mark.usefixtures("register_subman")
def test_archive_structure(insights_client):
    """
    Test that the archive have the correct structure
    """
    dirs_list = [
        "blacklist_report",
        "branch_info",
        "data",
        "egg_release",
        "insights_archive.txt",
        "meta_data",
        "version_info",
    ]

    subdirs_list = [
        "branch_info",
        "version_info",
        "boot",
        "etc",
        "insights_commands",
        "proc",
        "run",
        "sys",
        "usr",
        "var",
    ]

    insights_client.register()
    insights_client.run("--no-upload")

    list_of_files = glob.glob(f"{ARCHIVE_CACHE_DIRECTORY}/*.tar.gz")
    latest_file = max(list_of_files, key=os.path.getctime)

    with tarfile.open(latest_file, "r:gz") as tar:
        tar.extractall(path="/var/cache/insights-client/", filter="data")
        directory_name = latest_file.replace(".tar.gz", "")

    extracted_dirs_files = os.listdir(directory_name)
    missing_dirs = [d for d in dirs_list if d not in extracted_dirs_files]
    assert not missing_dirs, f"Missing directories {missing_dirs}"

    data_dir_path = os.path.join(directory_name, "data")
    data_subdirs = os.listdir(data_dir_path)
    missing_subdirs = [d for d in subdirs_list if d not in data_subdirs]
    assert not missing_subdirs, f"Missing subdirectory {missing_subdirs}"
