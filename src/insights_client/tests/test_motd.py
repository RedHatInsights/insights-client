import os
import tempfile
import unittest
import unittest.mock

import pytest

import insights_client


class MockFS:
    """Mock filesystem.

    Ensures that the files required for the MOTD manipulation are created
    in a temporary directory instead of working with actual system files.
    """

    def __init__(self):
        self.dir = tempfile.TemporaryDirectory()

        # /etc/insights-client/insights-client.motd
        self.dir_src = unittest.mock.patch(
            "insights_client.MOTD_SRC", f"{self.dir.name}/src"
        )
        self.dir_src.start()

        # /etc/motd.d/insights-client
        self.dir_motd = unittest.mock.patch(
            "insights_client.MOTD_FILE", f"{self.dir.name}/motd"
        )
        self.dir_motd.start()

        # /etc/insights-client/.registered
        self.dir_reg = unittest.mock.patch(
            "insights_client.REGISTERED_FILE", f"{self.dir.name}/reg"
        )
        self.dir_reg.start()

        # /etc/insights-client/.unregistered
        self.dir_unreg = unittest.mock.patch(
            "insights_client.UNREGISTERED_FILE", f"{self.dir.name}/unreg"
        )
        self.dir_unreg.start()

        with open(f"{self.dir.name}/src", "w") as f:
            f.write("This is the content of the MOTD file.")

    def __del__(self) -> None:
        self.dir_unreg.stop()
        self.dir_reg.stop()
        self.dir_motd.stop()
        self.dir_src.stop()
        self.dir = None


@pytest.fixture
def mock_fs():
    fs = MockFS()
    yield fs
    del fs


def test_present(mock_fs):
    assert not os.path.exists(insights_client.MOTD_FILE)

    # The file gets created/symlinked when .registered & .unregistered do not exist
    insights_client.update_motd_message()
    assert os.path.exists(insights_client.MOTD_FILE)
    assert os.path.samefile(insights_client.MOTD_FILE, insights_client.MOTD_SRC)


def test_absent_on_dot_registered(mock_fs):
    # The MOTD file exists by default
    insights_client.update_motd_message()
    assert os.path.exists(insights_client.MOTD_FILE)

    # It gets removed when .registered exists
    with open(f"{mock_fs.dir.name}/reg", "w") as f:
        f.write("")
    insights_client.update_motd_message()
    assert not os.path.exists(insights_client.MOTD_FILE)

    # It stays absent when run multiple times
    insights_client.update_motd_message()
    assert not os.path.exists(insights_client.MOTD_FILE)


def test_absent_on_dot_unregistered(mock_fs):
    # The MOTD file exists by default
    insights_client.update_motd_message()
    assert os.path.exists(insights_client.MOTD_FILE)

    # It gets removed when .unregistered exists
    with open(f"{mock_fs.dir.name}/unreg", "w") as f:
        f.write("")
    insights_client.update_motd_message()
    assert not os.path.exists(insights_client.MOTD_FILE)

    # It stays absent when run multiple times
    insights_client.update_motd_message()
    assert not os.path.exists(insights_client.MOTD_FILE)


def test_ignored_on_dev_null(mock_fs):
    # When the /etc/motd.d/insights-client is a symbolic link to /dev/null...
    os.symlink(os.devnull, f"{mock_fs.dir.name}/motd")

    # ...it should not be overwritten...
    insights_client.update_motd_message()
    assert os.path.samefile(os.devnull, f"{mock_fs.dir.name}/motd")

    # ...whether the MOTD file should be present or not.
    with open(f"{mock_fs.dir.name}/reg", "w") as f:
        f.write("")
    insights_client.update_motd_message()
    assert os.path.samefile(os.devnull, f"{mock_fs.dir.name}/motd")
