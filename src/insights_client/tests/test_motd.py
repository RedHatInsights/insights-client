import os
import pathlib
import tempfile
import typing
import unittest
import unittest.mock

import pytest

import insights_client


class MockFS:
    """Mock filesystem.

    Ensures that the files required for the MOTD manipulation are created
    in a temporary directory instead of working with actual system files.
    """

    _dir: tempfile.TemporaryDirectory

    @property
    def _chroot(self) -> pathlib.Path:
        return pathlib.Path(self._dir.name)

    def touch(self, path: str):
        (self._chroot / path).open("w").close()

    def exists(self, path: str) -> bool:
        return (self._chroot / path).exists()

    def symlink_to(self, path: str, point_to: str):
        (self._chroot / path).symlink_to(point_to)

    def samefile(self, first: str, second: str) -> bool:
        return (self._chroot / first).samefile(self._chroot / second)

    def __init__(self):
        self._dir = tempfile.TemporaryDirectory(prefix="test-chroot-")

        paths: typing.Dict[str, str] = {
            "insights_client.MOTD_SRC": "etc/insights-client/insights-client.motd",
            "insights_client.MOTD_FILE": "etc/motd.d/insights-client",
            "insights_client.REGISTERED_FILE": "etc/insights-client/.registered",
            "insights_client.UNREGISTERED_FILE": "etc/insights-client/.unregistered",
        }

        self.patches: typing.List[unittest.mock.patch] = []
        for target, path in paths.items():
            mocked_path = self._chroot / path
            mocked_path.parent.mkdir(parents=True, exist_ok=True)
            patch = unittest.mock.patch(target, f"{mocked_path!s}")
            self.patches.append(patch)
            patch.start()

        self.touch("etc/insights-client/insights-client.motd")

    def __del__(self):
        for patch in self.patches:
            patch.stop()
        self._dir.cleanup()


@pytest.fixture(scope="function")
def mock_fs():
    fs = MockFS()
    yield fs
    del fs


def test_present(mock_fs):
    assert not mock_fs.exists("etc/motd.d/insights-client")

    # The file gets created/symlinked when .registered & .unregistered do not exist
    insights_client.update_motd_message()
    assert mock_fs.exists("etc/motd.d/insights-client")
    assert mock_fs.samefile(
        "etc/motd.d/insights-client", "etc/insights-client/insights-client.motd"
    )


@pytest.mark.parametrize(
    "filename",
    [".registered", ".unregistered"],
)
def test_absent_on_dot(mock_fs, filename):
    # The MOTD gets created by default...
    insights_client.update_motd_message()
    assert mock_fs.exists("etc/motd.d/insights-client")

    # ...and gets removed when .registered/.unregistered exists.
    mock_fs.touch(f"etc/insights-client/{filename}")

    insights_client.update_motd_message()
    assert not mock_fs.exists("etc/motd.d/insights-client")

    # ...and it stays absent when run multiple times.
    insights_client.update_motd_message()
    assert not mock_fs.exists("etc/motd.d/insights-client")


def test_ignored_on_dev_null(mock_fs):
    # When the /etc/motd.d/insights-client is a symbolic link to /dev/null...
    mock_fs.symlink_to("etc/motd.d/insights-client", os.devnull)

    # ...it should not be overwritten...
    insights_client.update_motd_message()
    assert mock_fs.samefile("etc/motd.d/insights-client", os.devnull)

    # ...whether the MOTD file should be present or not.
    mock_fs.touch("etc/insights-client/.registered")
    insights_client.update_motd_message()
    assert mock_fs.samefile("etc/motd.d/insights-client", os.devnull)
