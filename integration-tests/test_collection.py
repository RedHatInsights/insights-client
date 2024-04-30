import contextlib
import os
import tarfile


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
