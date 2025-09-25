import pathlib
import sys
from unittest import mock


def pytest_configure(config):
    repo_root = pathlib.Path(__file__).parents[3]

    # Mock the insights package before any imports happen
    sys.modules["insights"] = mock.MagicMock()
    sys.modules["insights.client"] = mock.MagicMock()
    sys.modules["insights.client.phase"] = mock.MagicMock()
    sys.modules["insights.client.phase.v2"] = mock.MagicMock()
    sys.modules["insights.client.config"] = mock.MagicMock()

    # Hijack sys.path, so we don't have to use 'PYTHONPATH=src/'
    sources: pathlib.Path = repo_root / "src"
    sys.path.insert(0, str(sources))
