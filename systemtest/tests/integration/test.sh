#!/bin/bash
set -u
set -x

# get to project root
cd ../../../

# runs the packit setup
rpm -q insights-client || ./systemtest/guest-setup.sh

dnf --setopt install_weak_deps=False install -y \
  podman git-core python3-pip python3-pytest logrotate bzip2

python3 -m venv venv
# shellcheck disable=SC1091
. venv/bin/activate

pip install -r integration-tests/requirements.txt

pytest --junit-xml=./junit.xml -v integration-tests
retval=$?

if [ -d "$TMT_PLAN_DATA" ]; then
  cp ./junit.xml "$TMT_PLAN_DATA/junit.xml"
fi

exit $retval
