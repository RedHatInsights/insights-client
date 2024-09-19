"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: sst_csi_client_tools
:caseautomation: Automated
:upstream: Yes
"""

import os
import pytest
import conftest

pytestmark = pytest.mark.usefixtures("register_subman")


def test_upload_pre_collected_archive(insights_client, tmp_path):
    """
    :id: 9eba5a67-d013-4d43-98c7-c41ed38bcede
    :title: Test Upload of Pre-Collected Archive
    :description:
        This test verifies that a pre-collect insights-archive
        can be uploaded using --payload operation.
    :tier: Tier 1
    :steps:
        1. Register insights-client
        2. Run insights-client in an offline mode to generate an archive
            and save it
        3. Run the insights-client with the --payload option and valid --content-type
        4. Verify the successful upload of the archive
    :expectedresults:
        1. Insights-client is registered
        2. The archive is successfully generated and saved
        3. The upload process starts and the output message is as expected
        4. The upload completes successfully with the message as expected
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
    """
    :id: bb9ee84a-d262-4c42-ae16-9b45bf5a385c
    :title: Test Upload with Wrong Content Type
    :description:
        This test verifies that uploading an archive with wrong content
        type throws appropriate error message. Generate an archive and upload using
        --payload but wrong --content-type
    :tier: Tier 1
    :steps:
        1. Register insights-client
        2. Run the insights-client in offline mode to generate an archive and save it
        3. Run the insights-client with --payload option and invalid --content-type
        4. Run the insigts-client with a valid --content-type but different from
            compressor used
    :expectedresults:
        1. Insights-client is registered
        2. The archive is generated and saved
        3. The upload process fails with the appropriate message
        4. The upload process fails with the appropriate message
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
    """
    :id: bb9ee84a-d262-4c42-ae16-9b45bf5a385c
    :title: Test Upload of Too Large Archive
    :description:
        This test verifies that an attempt to upload too large archive
        results in failure
    :tier: Tier 1
    :steps:
        1. Register insights-client
        2. Create a large archive file in the temporary directory
        3. Run insights-client with --payload option and --content-type
            pointing to the archive
    :expectedresults:
        1. Insights-client is registered
        2. A large archive is created in the temporary directory
        3. The upload process fails with an appropriate message
    """
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
    :id: 69a06826-6093-46de-a7a6-9726ae141820
    :title: Test upload with Different Compressor Options
    :description:
        This test verifies that valid compression types can be used
        with --compressor to create archives and upload data using --payload
    :tier: Tier 1
    :steps:
        1. Register insights-client
        2. Run insights-client with --compressor option to generate an archive
            with specified type
        3. Verify the archive has the correct file extension based on the compression
            type
    :expectedresults:
        1. Insights-client is registered
        2. The archive is successfully generated
        3. The file has expected file extension
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
    :id: dafeb86e-463e-42fd-88e5-4551f1ba8f66
    :title: Test Retries on Upload Failure
    :description:
        This test verifies that client tries to upload archive if upload
        fails. Setting retries to 2 only because between each attempt the wait time is
        180 sec. Set wrong base_url in insights-client.config to fail upload operation
    :tier: Tier 1
    :steps:
        1. Register insights-client
        2. Save the archive
        3. Modify the configuration to use a non-existent base URL
        4. Run insights-client with --payload option specifying --retry=2
            to attempt upload twice
        5. verify the retry mechanism
        6. verify the final failure message
    :expectedresults:
        1. Insights-client is registered
        2. Archive is saved
        3. The configuration is modified and saved
        4. The command is run
        5. Each of the retry failed with expected error message
        6. the final error message is as expected
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
    :id: 1d740d1c-e98b-4571-86ac-10a233ff65ce
    :title: Test No Retries on Uncoverable Errors
    :description:
        This test verifies that client retries won't happen during
        unrecoverable errors. The client should try to upload just once and then fail.
    :tier: Tier 1
    :steps:
        1. Register insights-client
        2. Save the archive
        3. Run insights-client with --payload option specifying invalid --content-type
        4. Verify the output of the command
        5. Verify no-retries occur
    :expectedresults:
        1. Insights-client is registered
        2. Archive is saved
        3. The command is run
        4. The process fails with an appropriate message
        5. No retries occurred
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
