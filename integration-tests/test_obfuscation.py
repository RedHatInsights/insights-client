"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: sst_csi_client_tools
:caseautomation: Automated
:upstream: Yes
"""

import pytest
import tarfile
import logging
import uuid
import socket

pytestmark = pytest.mark.usefixtures("register_subman")


def test_ip_obfuscation(insights_client, tmp_path):
    """
    :id: 59c073f7-d207-42ae-85ee-a7a5d6fc6f8d
    :title: Test IP obfuscation functionality
    :description:
        This test verifies that when IP obfuscation is enabled in the
        insights-client configuration, the system's IP address is not
        present in the collected archive
    :reference:
    :tags: Tier 1
    :steps:
        1. Record the system's IP address
        2. Disable obfuscation in the configuration
        3. Run the insights-client and check archive for an IP address
        4. Enable obfuscation in the configuration
        5. Run the insights-client and check archive for an IP address
    :expectedresults:
        1. The system's IP address is recorded
        2. Configuration is updated and saved
        3. The IP address is found in the collected archive
        4. Configuration is updated and saved
        5. The IP address is not found in the collected archive
    """
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
    """
    :id: 68196220-f633-4a40-8040-6924d0e71b46
    :title: Test hostname obfuscation functionality
    :description:
        This test verifies that when hostname obfuscation is enabled in the
        insights-client configuration, the system's hostname is not present
        in the collected archive
    :reference:
    :tags: Tier 1
    :steps:
        1. Record the system's hostname
        2. Disable hostname obfuscation in the configuration
        3. Run the insights-client and check archive for a hostname
        4. Enable hostname obfuscation in the configuration
        5. Run the insights-client and check archive for a hostname
    :expectedresults:
        1. The system's hostname is recorded
        2. Configuration is updated and saved
        3. The hostname is found in the collected archive
        4. Configuration is updated and saved
        5. The hostname is not found in the collected archive
    """
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
    :id: ad3f22b2-8792-45fb-abdd-d29d58db5c41
    :title: Test password obfuscation in collected files
    :description:
        This test ensures that sensitive information such as passwords is obfuscated
        in collected files, regardless of the obfuscation setting in the configuration
        file
    :reference:
    :tags: Tier 1
    :steps:
        1. Backup the original content of the test file
        2. Append a password string to the test file
        3. Make sure obfuscation is disabled in the configuration file
        4. Run the insights-client and check for the password in the archive
        5. Enable obfuscation
        6. Run the insights-client and check for the password in the archive
        7. Restore the original content of the test file
    :expectedresults:
        1. Original content is backed up
        2. Password string is added without errors
        3. Configuration is updated and saved
        4. Password is not found in the test file
        5. Configuration is updated and saved
        6. Password is still not present in the test file
        7. Original content is restored
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
    """
    :id: aa2eb4cf-9fed-4fe9-8423-87bbf2f2dd95
    :title: Test package versions are not obfuscated when obfuscation is enabled
    :description:
        This test ensures that version strings in package information files
        are not incorrectly obfuscated as IP addresses when obfuscation is
        enabled
    :reference: https://issues.redhat.com/browse/ESSNTL-444
    :tags: Tier 1
    :steps:
        1. Enable obfuscation in the configuration file
        2. Run the insights-client and collect the archive
        3. Check the specified package information files in the archive
    :expectedresults:
        1. Configuration is updated and saved
        2. Archive is collected
        3. Version strings are not obfuscated and are present
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
    :id: a5b73cba-928d-4e78-9792-6a667e5c4c2b
    :title: Test display_name is not obfuscated when obfuscation is enabled
    :description:
        This test ensures that display_name in package information files
        are not incorrectly obfuscated as IP addresses when obfuscation is
        enabled
    :reference:
    :tags: Tier 1
    :steps:
        1. Enable obfuscation in the configuration file
        2. Run the insights-client and collect the archive
        3. Check the display_name information in the archive
    :expectedresults:
        1. Configuration is updated and saved
        2. Archive is collected
        3. Display_name is not obfuscated and is present
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
