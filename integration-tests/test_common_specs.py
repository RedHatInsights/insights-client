import json
import os
import pytest
import platform

pytestmark = pytest.mark.usefixtures("register_subman")


def test_common_specs(insights_client, tmp_path):
    """
    Verify that the specified specs can be collected and parsed as expected.
    Ref: https://issues.redhat.com/browse/RHINENG-10737
    """
    common_specs = [
        "insights.specs.Specs.date.json",
        "insights.specs.Specs.fstab.json",
        "insights.specs.Specs.hostname.json",
        "insights.specs.Specs.hosts.json",
        "insights.specs.Specs.installed_rpms.json",
        "insights.specs.Specs.ip_addresses.json",
        "insights.specs.Specs.ls_dev.json",
        "insights.specs.Specs.lscpu.json",
        "insights.specs.Specs.meminfo.json",
        "insights.specs.Specs.mount.json",
        "insights.specs.Specs.mountinfo.json",
        "insights.specs.Specs.ps_auxcww.json",
        "insights.specs.Specs.redhat_release.json",
        "insights.specs.Specs.uname.json",
        "insights.specs.Specs.yum_repos_d.json",
    ]
    if platform.machine() == "x86_64" or platform.machine() == "aarch64":
        common_specs.extend(
            [
                "insights.specs.Specs.dmidecode.json",
                "insights.specs.Specs.lspci.json",
            ]
        )

    # Running insights-client to collect data in tmp path
    insights_client.run(f"--output-dir={tmp_path}")

    # assert  that spec file exist and content has no error
    for spec in common_specs:
        spec_filepath = tmp_path / "meta_data" / spec
        assert os.path.exists(spec_filepath), f"spec file {spec} not found "
        with open(spec_filepath, "r") as specfile:
            data = json.load(specfile)
            assert not data["errors"], f"spec file contains error {data['errors']} "
            assert data["results"] is not None, "spec file exists but results are none."
