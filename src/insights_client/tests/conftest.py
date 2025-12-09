import os
import pathlib
import sys


def pytest_configure(config):
    repo_root = pathlib.Path(__file__).parents[3]

    # Hijack sys.path, so we don't have to use 'PYTHONPATH=src/'
    sources: pathlib.Path = repo_root / "src"
    sys.path.insert(0, str(sources))

    # Point us to the RPM egg, if it hasn't been specified outside
    if "EGG" not in os.environ:
        os.environ["EGG"] = str((repo_root / "data" / "rpm.egg").resolve())

    # We have to push the EGG into PATH immediately.
    # It would have been done by the client on its own, but we need to mock out
    # some of the internal functions (see `test_client.py`), and for that we need
    # the egg to already be present.
    sys.path.insert(0, os.environ["EGG"])

    # Move the temporary directories outside /var/lib/insights/.
    import insights_client

    insights_client.TEMPORARY_GPG_HOME_PARENT_DIRECTORY = "/tmp/"
    # Point to the actual key we ship to be able to actually verify the bundled egg.
    insights_client.GPG_KEY = str((repo_root / "data" / "redhattools.pub.gpg").resolve())
