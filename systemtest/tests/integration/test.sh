#!/bin/bash
set -eu
set -x

# get to project root
cd ../../../

dnf --setopt install_weak_deps=False install -y \
  podman git-core python3-pip python3-pytest

python3 -m venv venv
# shellcheck disable=SC1091
. venv/bin/activate

pip install -r integration-tests/requirements.txt

pytest -v integration-tests
