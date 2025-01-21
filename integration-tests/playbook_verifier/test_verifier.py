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
    """insights-client contains playbook verifier application.

    It is used by rhc-worker-playbook and rhc-worker-script to safely deliver
    and run Red Hat signed playbooks.

    In this test, the official playbooks are verified against the GPG key
    the application ships.
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
