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
def test_official_playbook(filename: str):
    """insights-client contains playbook verifier application.

    It is used by rhc-worker-playbook and rhc-worker-script to safely deliver
    and run Red Hat signed playbooks.

    In this test, the official playbooks are verified against the GPG key
    the application ships.
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
