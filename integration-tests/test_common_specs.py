"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import json
import os
import pytest
import subprocess
import logging

pytestmark = pytest.mark.usefixtures("register_subman")


@pytest.mark.skipif(
    os.uname().machine != "x86_64",
    reason="Test only runs on x86_64 architecture for now",
)
@pytest.mark.tier1
def test_common_specs(insights_client, tmp_path):
    """
    :id: 9010f731-ca05-4abb-b119-de9730b055c1
    :title: Test common specs
    :description:
        This test verifies that the specified specs can be collected,
        parsed and contain valid data without errors
    :tags: Tier 1
    :steps:
        1. Define the list of common specs to be tested
        2. Run the insights-client to collect data and save it in the
            specified temporary directory
        3. For each spec in the list check that it exists in the
            correct location
        4. Verify the spec file contains no errors
        5. Verify the spec file has valid results
    :expectedresults:
        1. The list of specs is correctly defined
        2. The client runs and the data is saved in the tmp_path directory
        3. Each spec file is found in the meta_data directory and none is missing
        4. Data contains no errors (data["errors"] is empty or does not exist)
        5. Each spec contains valid results (data["results"] is not None) confirming
            the data was successfully collected
    """
    common_specs = [
        "insights.specs.Specs.date.json",
        "insights.specs.Specs.hosts.json",
        "insights.specs.Specs.installed_rpms.json",
        "insights.specs.Specs.lscpu.json",
        "insights.specs.Specs.lspci.json",
        "insights.specs.Specs.meminfo.json",
        "insights.specs.Specs.mount.json",
        "insights.specs.Specs.mountinfo.json",
        "insights.specs.Specs.ps_auxcww.json",
        "insights.specs.Specs.redhat_release.json",
        "insights.specs.Specs.uname.json",
        "insights.specs.Specs.yum_repos_d.json",
    ]
    # The following specs can't be collected in containers
    privileged_specs = [
        "insights.specs.Specs.dmidecode.json",
        "insights.specs.Specs.fstab.json",
        "insights.specs.Specs.hostname.json",
        "insights.specs.Specs.ip_addresses.json",
    ]

    # Running insights-client to collect data in tmp path
    insights_client.run(f"--output-dir={tmp_path}")

    in_container: bool = "container" in os.environ.keys()
    for spec in common_specs + privileged_specs:
        spec_filepath = tmp_path / "meta_data" / spec

        # assert that spec file exists
        assert os.path.exists(spec_filepath), f"spec file {spec} not found "

        with open(spec_filepath, "r") as specfile:
            data = json.load(specfile)

        # assert that a spec doesn't contain errors
        # (unless we are in container and the spec is known to not work in containers)
        if in_container and spec in privileged_specs:
            continue

        try:
            assert not data["errors"], f"'{spec}' contains errors: {data['errors']} "
            assert data["results"] is not None, f"'{spec}' does not contain results"
        except AssertionError as e:
            logging.error(f"Spec '{spec}' failed with an error '{str(e)}'")

            # Try to extract and re-run the command from the spec JSON
            cmd = data["results"]["object"]["cmd"]
            if cmd:
                logging.debug(f"Attempting to re-run the cmd from the spec: '{cmd}'")
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=10
                )

                logging.debug(f"Command return code: {result.returncode}")
                logging.debug(f"Command STDOUT code: {result.stdout.strip()}")
                logging.debug(f"Command STDERR code: {result.stderr.strip()}")

                if result.returncode != 0:
                    raise AssertionError(
                        f"Command '{cmd}' failed with a return code \
                                         of {result.returncode}"
                    )
            else:
                logging.debug(f"No command found in spec JSON for {spec}")
            raise
