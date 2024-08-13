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
def test_motd(insights_client):
    """MOTD only exists on unregistered system without (.un)registered files."""
    # If the system is not registered, the file should be present.
    insights_client.run("--status")
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
def test_motd_dev_null(insights_client):
    """MOTD should not be touched if it is a /dev/null symlink."""
    with contextlib.ExitStack() as stack:
        os.symlink(os.devnull, MOTD_PATH)
        stack.callback(os.unlink, MOTD_PATH)

        insights_client.run("--status")
        assert os.path.samefile(os.devnull, MOTD_PATH)

        insights_client.register()
        assert conftest.loop_until(lambda: insights_client.is_registered)
        assert os.path.samefile(os.devnull, MOTD_PATH)

        insights_client.unregister()
        assert os.path.samefile(os.devnull, MOTD_PATH)


@pytest.mark.usefixtures("delete_special_files")
def test_motd_message():
    """
    On a unregistered system, the registration instructions should
        provide the users with complete instructions on:
        1. how to register their system using rhc
        2. what is rhc and what is Red Hat Insights.
        Ref: https://issues.redhat.com/browse/CCT-264
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
