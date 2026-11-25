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
  rpm -q insights-client > /dev/null || ./systemtest/guest-setup.sh

  # In most cases these should already be installed by tmt, see systemtest/plans/main.fmf
  dnf --setopt install_weak_deps=False install -y \
    podman git-core python3-pip python3-pytest logrotate bzip2 zip \
    scap-security-guide openscap-scanner openscap bzip2-devel
fi

# If SETTINGS_URL is set (most likely in .testing-farm.yaml), download the
# settings file from the provided URL. The served file is sanitized: it
# carries non-secret values directly and secret values as @vault:
# sentinels, which pytest-client-tools resolves at config load through the
# Vault AppRole delivered as VAULT_* environment variables (see README.md,
# "Integration test configuration"); PYTEST_CLIENT_TOOLS_* environment
# variables override any resolved value. Back up any existing settings.toml
# before downloading.
if [[ -v SETTINGS_URL ]]; then
  [ -f ./settings.toml ] && mv ./settings.toml ./settings.toml.bak
  if ! curl -f "$SETTINGS_URL" -o ./settings.toml; then
    echo "ERROR: Failed to download settings from: $SETTINGS_URL" >&2
    exit 1
  fi
  # Strict mode: an @vault: sentinel that cannot be resolved fails loud at
  # config load instead of degrading into a misleading validator error.
  # Inert while the served file carries no sentinels.
  export PYTEST_CLIENT_TOOLS_VAULT_REQUIRED=1
fi

python3 -m venv venv
# shellcheck disable=SC1091
. venv/bin/activate

pip install -r integration-tests/requirements.txt

# Print versions of packages that are actively being tested
rpm -q insights-client insights-core selinux-policy || true

# The sanitized settings file provides candlepin.username without the
# password, and pytest-client-tools requires candlepin.password whenever
# candlepin.username exists; activation keys satisfy the is_external check
# but not that validator. The fallback below only serves MANUAL runs
# against the containerized candlepin (ENV_FOR_DYNACONF=testing): no CI
# job sets ENV_FOR_DYNACONF=testing — CI jobs pick their environment at
# Testing Farm request time. It falls back to the container's well-known
# credentials; credentials for real environments must be supplied through
# PYTEST_CLIENT_TOOLS_* environment variables.
if [[ "${ENV_FOR_DYNACONF:-}" = "testing" ]]; then
  # Suppress tracing: Testing Farm masks only the values it injected
  # itself, so an operator-supplied real password must not reach the log.
  { set +x; } 2>/dev/null
  export PYTEST_CLIENT_TOOLS_CANDLEPIN__USERNAME="${PYTEST_CLIENT_TOOLS_CANDLEPIN__USERNAME:-admin}"
  export PYTEST_CLIENT_TOOLS_CANDLEPIN__PASSWORD="${PYTEST_CLIENT_TOOLS_CANDLEPIN__PASSWORD:-admin}"
  set -x
fi

pytest --log-level debug --junit-xml=./junit.xml -v integration-tests ${PYTEST_FILTER:+-k "${PYTEST_FILTER}"}
retval=$?

if [ -d "$TMT_PLAN_DATA" ]; then
  cp ./junit.xml "$TMT_PLAN_DATA/junit.xml"
  cp -r ./artifacts "$TMT_PLAN_DATA/"
fi

exit $retval
