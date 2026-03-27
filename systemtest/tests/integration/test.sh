#!/bin/bash
set -ux

# get to project root
cd ../../../

is_bootc() {
  command -v bootc > /dev/null &&
    ! bootc status --format=humanreadable | grep -q 'System is not deployed via bootc'
}

if ! is_bootc; then
  # TEST_RPMS is set in jenkins jobs after parsing CI Messages in gating Jobs.
  # If TEST_RPMS is set then install the RPM builds for gating.
  if [[ -v TEST_RPMS ]]; then
    echo "Installing RPMs: ${TEST_RPMS}"
    dnf -y install --allowerasing ${TEST_RPMS}
  fi

  # Simulate the packit setup on downstream builds.
  # This is for ad-hoc and compose testing.
  rpm -q insights-client || ./systemtest/guest-setup.sh
fi

# Override settings if provided and available.
if [ -n "${SETTINGS_URL+x}" ] && curl -I "$SETTINGS_URL" > /dev/null 2>&1; then
  [ -f ./settings.toml ] && mv ./settings.toml ./settings.toml.bak
  curl "$SETTINGS_URL" -o ./settings.toml
fi

python3 -m venv venv
# shellcheck disable=SC1091
. venv/bin/activate

pip install -r integration-tests/requirements.txt

pytest --log-level debug --junit-xml=./junit.xml -v integration-tests ${PYTEST_FILTER:+-k "${PYTEST_FILTER}"}
retval=$?

if [ -d "$TMT_PLAN_DATA" ]; then
  cp ./junit.xml "$TMT_PLAN_DATA/junit.xml"
  if [ -d ./artifacts ]; then
    cp -r ./artifacts "$TMT_PLAN_DATA/"
  fi
fi

exit $retval
