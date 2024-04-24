import os

import pytest
import conftest

pytestmark = pytest.mark.usefixtures("register_subman")


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
