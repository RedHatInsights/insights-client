"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import re
import pytest

from pytest_client_tools.util import Version
from constants import INSIGHTS_CLIENT_LOG_FILE


@pytest.mark.tier1
def test_version(insights_client):
    """
    :id: 7ec671cb-39ae-4cda-b279-f05d7c835d5d
    :title: Test --version outputs client and core versions
    :description:
        This test verifies that running `insights-client --version` outputs
        both the client and core version information
    :reference:
    :tags: Tier 1
    :steps:
        1. Run `insights-client --version`
        2. Check the output for "Client: " and "Core: "
    :expectedresults:
        1. Command executes without errors
        2. Both "Client: " and "Core: " are present in the output
    """
    proc = insights_client.run("--version", selinux_context=None)
    assert "Client: " in proc.stdout
    assert "Core: " in proc.stdout


@pytest.mark.usefixtures("register_subman")
@pytest.mark.parametrize("option", ["--status", "--checkin"])
@pytest.mark.tier1
def test_version_core_matches_runtime_egg(insights_client, option):
    """
    :id: 5fa66d8b-0304-450d-9ad7-c3170fe4bd07
    :title: Test --version Core matches the egg used by other commands
    :parametrized: yes
    :description:
        This test verifies that `insights-client --version` reports the same
        Core version as the egg used by other commands such as `--status` and
        `--checkin`, including when `/var/lib/insights/newest.egg` is present.
    :reference: https://issues.redhat.com/browse/RHEL-123603
    :tags: Tier 1
    :steps:
        1. Run `insights-client` with a runtime command (prefers newest.egg
           when available)
        2. Read the core version used by that command from the client log
        3. Run `insights-client --version` and compare Core to that version
    :expectedresults:
        1. The runtime command completes (registration status may vary)
        2. The client log contains a core version for the runtime command
        3. `--version` Core matches the core version used by the runtime command
    """
    insights_client.run(option, check=False, selinux_context=None)

    with open(INSIGHTS_CLIENT_LOG_FILE) as log_file:
        runtime_versions = re.findall(
            rf"version=([0-9.]+), phase=\w+, arguments={re.escape(option)}",
            log_file.read(),
        )
    assert runtime_versions, f"No {option} core version in {INSIGHTS_CLIENT_LOG_FILE}"

    assert insights_client.core_version == Version(runtime_versions[-1])
