import os
import json
import logging

import pytest
import conftest
from constants import HOST_DETAILS

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.usefixtures("register_subman")

def read_host_details():
    with open(HOST_DETAILS, "r") as data_file:
        return json.load(data_file)

def test_upload_pre_collected_archive(insights_client, tmp_path):
    """This test verifies that a pre-collect insights-archive can be uploaded
    using --payload operation.
    """

    archive_name = "archive.tar.gz"
    archive_location = tmp_path / archive_name

    # Registering the client because upload can happen on registered system
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    # Running insights-client in offline mode to generate archive and save at tmp dir
    insights_client.run(f"--output-file={archive_location}")

    # Running insights-client --payload with --content-type to upload archive
    # collected in previous step
    upload_result = insights_client.run(
        f"--payload={archive_location}", "--content-type=gz"
    )
    assert "Uploading Insights data." in upload_result.stdout
    assert "Successfully uploaded report" in upload_result.stdout


def test_upload_wrong_content_type(insights_client, tmp_path):
    """This test verifies that uploading an archive with wrong content
    type throws appropriate error message.
    Generate an archive and upload using --payload but wrong --content-type
    """
    archive_name = "archive.tar.gz"
    archive_location = tmp_path / archive_name

    # Registering the client because upload can happen on registered system
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    # Running insights-client in offline mode to generate archive and save at tmp dir
    insights_client.run(f"--output-file={archive_location}")

    # Running insights-client --payload with invalid --content-type to upload archive
    # collected in previous step
    upload_result = insights_client.run(
        f"--payload={archive_location}", "--content-type=bzip", check=False
    )
    assert "Invalid content-type." in upload_result.stdout

    # trying to upload with a valid content type but different from compressor
    upload_result = insights_client.run(
        f"--payload={archive_location}", "--content-type=xz", check=False
    )
    assert "Content type different from compression" in upload_result.stdout


def test_upload_too_large_archive(insights_client, tmp_path):
    """This test verifies that an attempt to upload too large archive
    results in failure."""

    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    file_path = tmp_path / "large_file.tar.gz"
    file_size = 100 * 1024 * 1024  # 100mb
    with open(file_path, "wb") as f:
        f.seek(int(file_size) + 1)
        f.write(b"\0")

    upload_result = insights_client.run(
        f"--payload={file_path}", "--content-type=gz", check=False
    )

    assert "Archive is too large to upload" in upload_result.stdout
    assert "Upload failed." in upload_result.stdout


@pytest.mark.parametrize(
    "compressor,expected_extension",
    [
        ("gz", ".gz"),
        ("bz2", ".bz2"),
        ("xz", ".xz"),
    ],
)
def test_upload_compressor_options(
    insights_client,
    compressor,
    expected_extension,
):
    """
    This test verifies that valid compression types can be used
    with --compressor to create archives and upload data using --payload
    """
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    # using --compressor option to generate and save archive
    command_result = insights_client.run(f"--compressor={compressor}", "--no-upload")
    archive_name = command_result.stdout.split()[-1]

    # Verifying that archive is created with expected extension
    assert os.path.splitext(archive_name)[1] == expected_extension
    assert (os.path.splitext(archive_name)[0]).endswith(".tar")

    # Now try to upload the pre-collected archive
    upload_result = insights_client.run(
        f"--payload={archive_name}", f"--content-type={compressor}"
    )
    assert "Uploading Insights data." in upload_result.stdout
    assert "Successfully uploaded report" in upload_result.stdout


def test_retries(insights_client):
    """
    This test verifies that client tries to upload archive if upload fails.
    setting retries to 2 only because between each attempt the wait time is 180 sec.
    set wrong base_url in insights-client.config to fail upload operation
    """
    reg_result = insights_client.run("--register", "--keep-archive")
    assert conftest.loop_until(lambda: insights_client.is_registered)

    # Save the archive, to be used while upload operation
    archive_name = reg_result.stdout.split()[-1]

    # Modifying config to break connection
    insights_client.config.auto_config = False
    insights_client.config.base_url = "non-existent-url.redhat.com"
    insights_client.config.save()

    # Now try to upload the pre-collected archive with retry=2 , default content=type gz
    upload_result = insights_client.run(
        f"--payload={archive_name}", "--content-type={gz}", "--retry=2", check=False
    )

    assert "Upload attempt 1 of 2 failed" in upload_result.stdout
    assert "Upload attempt 2 of 2 failed" in upload_result.stdout
    assert "Waiting 180 seconds then retrying" in upload_result.stdout
    assert "All attempts to upload have failed!" in upload_result.stdout


def test_retries_not_happening_on_unrecoverable_errors(insights_client):
    """
    This test verifies that client retries won't happen during unrecoverable errors.
    The client should try to upload just once and then fail.
    """
    reg_result = insights_client.run("--register", "--keep-archive")
    assert conftest.loop_until(lambda: insights_client.is_registered)

    # Save the archive, to be used while upload operation
    archive_name = reg_result.stdout.split()[-1]

    # Pass invalid content type to mock unrecoverable errors
    upload_result = insights_client.run(
        f"--payload={archive_name}",
        "--content-type=invalid-type",
        "--retry=2",
        check=False,
    )
    assert "Upload failed." in upload_result.stdout
    assert "Upload attempt 1 of 2 failed" not in upload_result.stdout

def test_upload_pre_collected_archive_creates_new_inventory_record(
        insights_client,
        tmp_path,
        subtests
):
    """This test verifies that a new inventory record is created
    after a pre-collect insights-archive is uploaded.
    
    This test extends a test `test_upload_pre_collected_archive`
    """
    # Registering the client because upload can happen on registered system
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)

    inventory_before_upload = read_host_details()
    logger.debug(f"inventory before upload: {inventory_before_upload}")
    
    with subtests.test(msg="Uploading pre-colected archive"):
        archive_name = "archive.tar.gz"
        archive_location = tmp_path / archive_name

        # Running insights-client in offline mode to generate archive and save at tmp dir
        insights_client.run(f"--output-file={archive_location}")

        # Running insights-client --payload with --content-type to upload archive
        # collected in previous step
        upload_result = insights_client.run(
            f"--payload={archive_location}", "--content-type=gz"
        )
        
    with subtests.test(msg="Verify that new invntory record is created"):
        inventory_after_upload = read_host_details()
        logger.debug(f"inventory after upload: {inventory_after_upload}")
