#!/bin/bash
set -u
set -x

# get to project root
cd ../../../

# Check for bootc/image-mode deployments which should not run dnf
if ! command -v bootc >/dev/null || bootc status | grep -q 'type: null'; then
  # Check for GitHub pull request ID and install build if needed.
  # This is for the downstream PR jobs.
  [ -z "${ghprbPullId+x}" ] || ./systemtest/copr-setup.sh

  # Simulate the packit setup on downstream builds.
  # This is for ad-hoc and compose testing.
  rpm -q insights-client || ./systemtest/guest-setup.sh

  dnf --setopt install_weak_deps=False install -y \
    podman git-core python3-pip python3-pytest logrotate bzip2 zip
fi

# If this is an insightsCore PR build and sign the new egg.
[ -z "${insightsCoreBranch+x}" ] || ./systemtest/insights-core-setup.sh

python3 -m venv venv
# shellcheck disable=SC1091
. venv/bin/activate

pip install -r integration-tests/requirements.txt

pytest --junit-xml=./junit.xml -v integration-tests
retval=$?

if [ -d "$TMT_PLAN_DATA" ]; then
  cp ./junit.xml "$TMT_PLAN_DATA/junit.xml"
  cp -r ./artifacts "$TMT_PLAN_DATA/"
fi

exit $retval
