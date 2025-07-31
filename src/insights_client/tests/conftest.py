import os
import pathlib
import sys


def pytest_configure(config):
    repo_root = pathlib.Path(__file__).parents[3]

    # Hijack sys.path, so we don't have to use 'PYTHONPATH=src/'
    sources: pathlib.Path = repo_root / "src"
    sys.path.insert(0, str(sources))
