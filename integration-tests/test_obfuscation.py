import pytest
import tarfile
import logging
import uuid
import socket

pytestmark = pytest.mark.usefixtures("register_subman")


def test_ip_obfuscation(insights_client, tmp_path):
    # Record the system ip
    hostname = socket.gethostname()
    system_ip = socket.gethostbyname(hostname)

    # Check the ip in archive before obfuscating ip
    insights_client.config.obfuscate = False
    insights_client.config.save()
    assert check_obfuscated_info(insights_client, tmp_path, system_ip)

    # Obfuscate hostname: obfuscate=True
    insights_client.config.obfuscate = True
    insights_client.config.save()

    # Check the ip in archive after obfuscating ip
    assert not check_obfuscated_info(insights_client, tmp_path, system_ip)


def test_hostname_obfuscation(insights_client, tmp_path):
    # Record the system hostname
    system_hostname = socket.gethostname()

    # Check the hostname in archive before obfuscating hostname
    insights_client.config.obfuscate = False
    insights_client.config.obfuscate_hostname = False
    insights_client.config.save()
    assert check_obfuscated_info(insights_client, tmp_path, system_hostname)

    # Check the hostname in archive after obfuscating hostname
    insights_client.config.obfuscate = True
    insights_client.config.obfuscate_hostname = True
    insights_client.config.save()
    assert not check_obfuscated_info(insights_client, tmp_path, system_hostname)


@pytest.mark.parametrize("password_file", ["/etc/redhat-release", "/etc/hosts"])
def test_password_obfuscation(insights_client, tmp_path, password_file):
    """
    Add an item of password in some files,
    no matter obfuscate=True or obfuscate=False in insights_client.conf,
    the password is not in the collected file and there are asterisks instead
    """
    # backup the original content of tested files
    with open(password_file, "r+") as f:
        original_content = f.read()
    try:
        # Add a line about password in a tested file
        password_string = "my-super-secret-password"
        with open(password_file, "a") as file:
            file.write(f"\npassword: {password_string}")

        # Make sure obfuscate=False
        insights_client.config.obfuscate = False
        insights_client.config.save()

        # the password value is not visible although obfuscate=False
        assert not check_obfuscated_info(insights_client, tmp_path, password_string)

        # the password  value is not visible after Obfuscating IP
        insights_client.config.obfuscate = True
        insights_client.config.save()
        assert not check_obfuscated_info(insights_client, tmp_path, password_string)
    finally:
        with open(password_file, "w+") as f:
            f.write(original_content)


@pytest.mark.parametrize(
    "package_info_file",
    [
        "data/insights_commands/rpm_-qa_--qf",
        "data/insights_commands/yum_-C_--noplugins_list_available",
        "data/insights_commands/yum_updates_list",
        "data/etc/dnf/modules.d/",
    ],
)
def test_no_obfuscation_on_package_version(
    insights_client, tmp_path, package_info_file
):
    """Test exclusion of certain Specs from IP address obfuscation:
    Examine the files produced by these Specs:
            • insights.specs.Specs.installed_rpms
            • insights.specs.Specs.dnf_modules
            • insights.specs.Specs.yum_list_available
            • insights.specs.Specs.yum_updates
    Verify that version strings consisting of four parts
         like shadow-utils-4.1.5.1-24.el7.x86_64 are not obfuscated
         as if they were IPv4 addresses. An obfuscated string would
         look like this: shadow-utils-10.230.230.21-24.el7.x86_64
    Related Bug: https://issues.redhat.com/browse/ESSNTL-444
    """
    # Obfuscate IP
    insights_client.config.obfuscate = True
    insights_client.config.save()

    # Check if the package version is obfuscated by IP obfuscation
    archive_name = "test_archive_" + str(uuid.uuid4()) + ".tar.gz"
    archive_location = tmp_path / archive_name
    insights_client.run("--register", "--output-file=%s" % archive_location)
    with tarfile.open(archive_location, "r") as tar:
        for w_file in tar.getmembers():
            if w_file.name.find(package_info_file) != -1:
                file_content = tar.extractfile(w_file).read()
                assert "10.230.230" not in file_content.decode()


def test_no_obfuscation_on_display_name(insights_client, tmp_path):
    """
    Check the ip obfuscation does not affect the display_name:
    method 1:
        (1) Set ip obfuscation
        (2) Run insights-client --display-name=xxx
        (3) Check the display_name on CRC: it shows correctly without obfuscation
    method 2:
        (1) Set ip obfuscation
        (2) Set the display_name in /etc/insights-client/insights-client.conf
        (3) Run insights-client --no-upload
        (4) Check the archive: display_name is not obfuscated
    """

    # Set IP obfuscation and set display_name in insights-client.conf
    display_name_setting = "test_display_name" + str(uuid.uuid4())
    insights_client.config.obfuscate = True
    insights_client.config.display_name = display_name_setting
    insights_client.config.save()

    # Check the display_name in the archive
    archive_name = "test_archive_" + str(uuid.uuid4()) + ".tar.gz"
    archive_location = tmp_path / archive_name
    insights_client.run("--register", "--output-file=%s" % archive_location)
    with tarfile.open(archive_location, "r") as tar:
        for w_file in tar.getmembers():
            if w_file.name.endswith("display_name"):
                file_content = tar.extractfile(w_file).read().decode()
                assert display_name_setting in file_content


def check_obfuscated_info(insights_client, tmp_path, info_to_search):
    archive_name = "test_archive_" + str(uuid.uuid4()) + ".tar.gz"
    archive_location = tmp_path / archive_name
    logging.info(archive_location)
    insights_client.run("--output-file=%s" % archive_location)
    info_exist = []
    with tarfile.open(archive_location, "r") as tar:
        for w_file in tar.getmembers():
            extracted_file = tar.extractfile(w_file)
            if (
                extracted_file is not None
                and info_to_search in extracted_file.read().decode()
            ):
                info_exist += [w_file.name]
        logging.info(info_exist)
        return info_exist
