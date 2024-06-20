#!/bin/bash
set -u
set -x

# get to project root
cd ../../../

# Check for GitHub pull request ID and install build if needed.
# This is for the downstream PR jobs.
[ -z "${ghprbPullId+x}" ] || ./systemtest/copr-setup.sh

# Simulate the packit setup on downstream builds.
# This is for ad-hoc and compose testing.
rpm -q insights-client || ./systemtest/guest-setup.sh

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
