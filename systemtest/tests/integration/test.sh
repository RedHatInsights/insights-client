#!/bin/bash
set -eu
set -x

. /etc/os-release
if test "${ID}" = fedora -a ${VERSION_ID} -ge 39; then
  # HACK
  # on newer gnupg import the key to the local keyring; this will be solved
  # once both insights-core and insights-client are fixed to not rely on
  # root's .gnupg directory:
  # - https://github.com/RedHatInsights/insights-core/pull/3930
  # - https://github.com/RedHatInsights/insights-client/pull/154
  gpg --import /etc/insights-client/redhattools.pub.gpg
fi

# get to project root
cd ../../../

dnf --setopt install_weak_deps=False install -y \
  podman git-core python3-pip python3-pytest

python3 -m venv venv
# shellcheck disable=SC1091
. venv/bin/activate

pip install -r integration-tests/requirements.txt

pytest -v integration-tests
