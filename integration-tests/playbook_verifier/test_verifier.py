"""
:casecomponent: insights-client
:requirement: RHSS-291297
:polarion-project-id: RHELSS
:polarion-include-skipped: false
:polarion-lookup-method: id
:subsystemteam: sst_csi_client_tools
:caseautomation: Automated
:upstream: Yes
"""

import pathlib
import subprocess
import sys
import pytest
from pytest_client_tools.util import Version


PLAYBOOK_DIRECTORY = pathlib.Path(__file__).parent.absolute() / "playbooks"


@pytest.mark.parametrize(
    "filename",
    [
        "insights_setup.yml",
        "compliance_openscap_setup.yml",
        "bugs.yml",
    ],
)
def test_official_playbook(insights_client, filename: str):
    """
    :id: 3659e27f-3621-4591-b1c4-b5f0a277bb72
    :title: Test playbook verifier
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
    if (
        sys.version_info >= (3, 12)
        and insights_client.core_version < Version(3, 5, 2)
        and filename == "bugs.yml"
    ):
        pytest.xfail(
            f"Core {insights_client.core_version} suffers from "
            "CCT-1065, CCT-1101, CCT-1102."
        )

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
