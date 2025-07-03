"""
:component: insights-client
:requirement: RHSS-291297
:polarion-project-id: RHELSS
:polarion-include-skipped: false
:polarion-lookup-method: id
:poolteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import pathlib
import subprocess
import sys
import pytest


PLAYBOOK_DIRECTORY = pathlib.Path(__file__).parent.absolute() / "playbooks"


@pytest.mark.xfail(
    condition=sys.version_info >= (3, 12),
    reason="Verification is known to be broken on Python 3.12+",
)
@pytest.mark.parametrize(
    "filename",
    [
        "insights_setup.yml",
        "compliance_openscap_setup.yml",
    ],
)
@pytest.mark.tier1
def test_official_playbook(filename: str):
    """
    :id: 3659e27f-3621-4591-b1c4-b5f0a277bb72
    :title: Test playbook verifier
    :parametrized: yes
    :description:
        This test verifies the official playbooks against the GPG key
        the application ships.
    :tags: Tier 1
    :steps:
        1. Read playbook file content
        2. Run insights-client verifier with playbook
        3. Compare output to input
    :expectedresults:
        1. File content is correctly read and loaded into memory
        2. Subprocess executes successfully without errors
        3. Verifier's output matches original playbook content
    """
    playbook_content: str = (PLAYBOOK_DIRECTORY / filename).read_text()

    result = subprocess.run(
        [
            "insights-client",
            "-m",
            "insights.client.apps.ansible.playbook_verifier",
            "--quiet",
            "--payload",
            "noop",
            "--content-type",
            "noop",
        ],
        input=playbook_content,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=True,
    )

    # The playbooks may and may not include newline as EOF.
    assert result.stdout.strip() == playbook_content.strip()
