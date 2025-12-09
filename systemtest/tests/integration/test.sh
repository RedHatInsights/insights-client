#!/bin/bash
set -u
set -x

# get to project root
cd ../../../

# Check for bootc/image-mode deployments which should not run dnf
if ! command -v bootc >/dev/null || bootc status | grep -q 'System is not deployed via bootc'; then
  # TEST_RPMS is set in jenkins jobs after parsing CI Messages in gating Jobs.
  # If TEST_RPMS is set then install the RPM builds for gating.
  if [[ -v TEST_RPMS ]]; then
    echo "Installing RPMs: ${TEST_RPMS}"
    dnf -y install --allowerasing ${TEST_RPMS}
  fi

  # Simulate the packit setup on downstream builds.
  # This is for ad-hoc and compose testing.
  rpm -q insights-client || ./systemtest/guest-setup.sh

  # In most cases these should already be installed by tmt, see systemtest/plans/main.fmf
  dnf --setopt install_weak_deps=False install -y \
    podman git-core python3-pip python3-pytest logrotate bzip2 zip \
    scap-security-guide openscap-scanner openscap bzip2-devel
fi

# If this is an insightsCore PR build and sign the new egg.
[ -z "${insightsCoreBranch+x}" ] || ./systemtest/insights-core-setup.sh

# If SETTINGS_URL is set (most likely in .testing-farm.yaml), download the settings
# file from the provided URL. Back up any existing settings.toml before downloading.
if [[ -v SETTINGS_URL ]]; then
  [ -f ./settings.toml ] && mv ./settings.toml ./settings.toml.bak
  if ! curl -f "$SETTINGS_URL" -o ./settings.toml; then
    echo "ERROR: Failed to download settings from: $SETTINGS_URL" >&2
    exit 1
  fi
fi

python3 -m venv venv
# shellcheck disable=SC1091
. venv/bin/activate

pip install -r integration-tests/requirements.txt

pytest --log-level debug --junit-xml=./junit.xml -v integration-tests ${PYTEST_FILTER:+-k "${PYTEST_FILTER}"}
retval=$?

if [ -d "$TMT_PLAN_DATA" ]; then
  cp ./junit.xml "$TMT_PLAN_DATA/junit.xml"
  cp -r ./artifacts "$TMT_PLAN_DATA/"
fi

exit $retval
