"""
:casecomponent: insights-client
:requirement: RHSS-291297
:polarion-project-id: RHELSS
:polarion-include-skipped: false
:polarion-lookup-method: id
:subsystemteam: sst_csi_client_tools
:caseautomation: Automated
:upstream: Yes
"""

import contextlib
import conftest
import os
import subprocess
import pytest


DOT_REGISTERED_PATH = "/etc/insights-client/.registered"
DOT_UNREGISTERED_PATH = "/etc/insights-client/.unregistered"

MOTD_PATH = "/etc/motd.d/insights-client"
MOTD_SRC = "/etc/insights-client/insights-client.motd"


@pytest.fixture
def delete_special_files():
    """Clean special files before and after test.

    Since .registered and .unregistered files are usually ignored and
    do not affect the behavior of insights-client, the MOTD case is
    special and depends on them.

    To ensure the tests here are not affected by them, we remove them
    """

    def delete_files():
        with contextlib.suppress(FileNotFoundError):
            os.remove(DOT_REGISTERED_PATH)
        with contextlib.suppress(FileNotFoundError):
            os.remove(DOT_UNREGISTERED_PATH)
        with contextlib.suppress(FileNotFoundError):
            os.remove(MOTD_PATH)

    delete_files()
    yield
    delete_files()


@pytest.mark.usefixtures("register_subman")
@pytest.mark.usefixtures("delete_special_files")
@pytest.mark.tier1
def test_motd(insights_client):
    """
    :id: a66a93bb-bbd2-4db0-a2aa-2bb184b11187
    :title: Test MOTD file presence based on registration status
    :description:
        This test verifies that the MOTD file exists on an unregistered
        system and that it is appropriately removed or not recreated upon
        registration and unregistration
    :reference:
    :tags: Tier 1
    :steps:
        1. Verify that MOTD file is present on an unregistered system
        2. Register the insights-client
        3. Verify the MOTD file does not exists after registration
        4. Unregister the insights-client
        5. Verify the MOTD file still does not exist after unregistration
    :expectedresults:
        1. The MOTD file is present
        2. The client registers successfully
        3. The MOTD file is removed
        4. The client unregisters successfully
        5. The MOTD file is still not present
    """
    # If the system is not registered, the file should be present.
    insights_client.run("--status", check=False)
    assert os.path.exists(MOTD_PATH)

    # After registration, the file should not exist.
    insights_client.register()
    assert conftest.loop_until(lambda: insights_client.is_registered)
    assert not os.path.exists(MOTD_PATH)

    # The system was unregistered. Because .unregistered file exists,
    # the file should not be present.
    insights_client.unregister()
    assert not os.path.exists(MOTD_PATH)


@pytest.mark.usefixtures("register_subman")
@pytest.mark.usefixtures("delete_special_files")
@pytest.mark.tier1
def test_motd_dev_null(insights_client):
    """
    :id: 7d48df16-e1af-4158-8a33-1d2cbb9ed22d
    :title: Test MOTD remains untouched when symlinked to /dev/null
    :description:
        This tst ensures that of the MOTD file is a symbolic link to
        /dev/null, it is not modified or removed during the client's registration
        and unregistration processes
    :reference:
    :tags: Tier 1
    :steps:
        1. Create a symlink from MOTD_PATH to /dev/null
        2. Run insights-client with --status option
        3. Register the insights-client
        4. Unregister the insights-client
    :expectedresults:
        1. The symlink is created successfully
        2. Command runs successfully and MOTD remains a symlink to /dev/null
        3. The client is registered and MOTD stayed unchanged
        4. the client is unregistered and MOTD stayed unchanged
    """
    with contextlib.ExitStack() as stack:
        os.symlink(os.devnull, MOTD_PATH)
        stack.callback(os.unlink, MOTD_PATH)

        insights_client.run("--status", check=False)
        assert os.path.samefile(os.devnull, MOTD_PATH)

        insights_client.register()
        assert conftest.loop_until(lambda: insights_client.is_registered)
        assert os.path.samefile(os.devnull, MOTD_PATH)

        insights_client.unregister()
        assert os.path.samefile(os.devnull, MOTD_PATH)


@pytest.mark.usefixtures("delete_special_files")
@pytest.mark.tier1
def test_motd_message():
    """
    :id: 56d12383-f7bb-4dbe-899c-a1cbd2172a30
    :title: Test MOTD message content for unregistered systems
    :description:
        This test ensures that on unregistered system, the MOTD provides users
        with complete instructions on how to register
    :reference: https://issues.redhat.com/browse/CCT-264
    :tags: Tier 1
    :steps:
        1. Ensure the host is unregistered
        2. Read the content of the MOTD file and verify that content matches
            the expected message
    :expectedresults:
        1. The system is unregistered
        2. The MOTD provides correct registration instructions
    """
    cmd = ["cat", MOTD_SRC]
    output = subprocess.check_output(cmd, universal_newlines=True)
    motd_msg = "Register this system with Red Hat Insights: rhc connect\n\n\
Example:\n\
# rhc connect --activation-key <key> --organization <org>\n\n\
The rhc client and Red Hat Insights will enable analytics and additional\n\
management capabilities on your system.\n\
View your connected systems at https://console.redhat.com/insights\n\n\
You can learn more about how to register your system \n\
using rhc at https://red.ht/registration\n"
    assert output == motd_msg
