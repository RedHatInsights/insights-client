import pytest
import re
import subprocess

pytestmark = pytest.mark.usefixtures("register_subman")


def test_common_specs(insights_client):
    common_specs = [
        "insights.specs.Specs.date",
        "insights.specs.Specs.dmidecode",
        "insights.specs.Specs.fstab",
        "insights.specs.Specs.hostname",
        "insights.specs.Specs.hosts",
        "insights.specs.Specs.installed_rpms",
        "insights.specs.Specs.ip_addresses",
        "insights.specs.Specs.ls_dev",
        "insights.specs.Specs.lscpu",
        "insights.specs.Specs.lspci",
        "insights.specs.Specs.meminfo",
        "insights.specs.Specs.mount",
        "insights.specs.Specs.mountinfo",
        "insights.specs.Specs.ps_auxcww",
        "insights.specs.Specs.redhat_release",
        "insights.specs.Specs.uname",
        "insights.specs.Specs.yum_repos_d",
    ]

    insights_client.register()
    output = insights_client.run("--no-upload")

    pattern = r"Archive saved at (.+/[^/]+\.tar\.gz)$"
    match = re.search(pattern, output.stdout, re.MULTILINE)
    archive_path = match.group(1)

    content = subprocess.run(
        "tar", "-xvzf", archive_path, text=True, capture_output=True
    )
    for spec in common_specs:
        assert spec in content.stdout
