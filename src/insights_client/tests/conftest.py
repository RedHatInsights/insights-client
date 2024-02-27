import os
import os.path
import sys


def pytest_configure(config):
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

    # Hijack sys.path, so we don't have to use 'PYTHONPATH=src/'
    sources = repo_root + "/src"
    sys.path.insert(0, str(sources))

    # Point us to the RPM egg, if it hasn't been specified outside
    if "EGG" not in os.environ:
        raise RuntimeError("The tests need 'EGG' egg in order to run.")

    # We have to push the EGG into PATH immediately.
    # It would have been done by the client on its own, but we need to mock out
    # some of the internal functions (see `test_client.py`), and for that we need
    # the egg to already be present.
    sys.path.insert(0, os.environ["EGG"])

    # Move the temporary directories outside /var/lib/insights/.
    import insights_client
    insights_client.TEMPORARY_GPG_HOME_PARENT_DIRECTORY = "/tmp/"
    # Point to the actual key we ship to be able to actually verify the bundled egg.
    insights_client.GPG_KEY = repo_root + "/data/redhattools.pub.gpg"
