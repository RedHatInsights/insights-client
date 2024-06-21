import contextlib
import os

import pytest


DOT_REGISTERED_PATH = "/etc/insights-client/.registered"
DOT_UNREGISTERED_PATH = "/etc/insights-client/.unregistered"

MOTD_PATH = "/etc/motd.d/insights-client"
MOTD_SRC = "/etc/insights-client/insights-client.motd"


pytestmark = pytest.mark.usefixtures("register_subman")


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


@pytest.mark.usefixtures("delete_special_files")
def test_motd(insights_client):
    """MOTD only exists on unregistered system without (.un)registered files."""
    # If the system is not registered, the file should be present.
    insights_client.run("--status")
    assert os.path.exists(MOTD_PATH)

    # After registration, the file should not exist.
    insights_client.register()
    assert not os.path.exists(MOTD_PATH)

    # The system was unregistered. Because .unregistered file exists,
    # the file should not be present.
    insights_client.unregister()
    assert not os.path.exists(MOTD_PATH)


@pytest.mark.usefixtures("delete_special_files")
def test_motd_dev_null(insights_client):
    """MOTD should not be touched if it is a /dev/null symlink."""
    with contextlib.ExitStack() as stack:
        os.symlink(os.devnull, MOTD_PATH)
        stack.callback(os.unlink, MOTD_PATH)

        insights_client.run("--status")
        assert os.path.samefile(os.devnull, MOTD_PATH)

        insights_client.register()
        assert os.path.samefile(os.devnull, MOTD_PATH)

        insights_client.unregister()
        assert os.path.samefile(os.devnull, MOTD_PATH)
