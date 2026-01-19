"""
:casecomponent: insights-client
:requirement: RHSS-291297
:subsystemteam: rhel-sst-csi-client-tools
:caseautomation: Automated
:upstream: Yes
"""

import os
import pytest
import contextlib
import subprocess
from pytest_client_tools.util import Version, loop_until
from constants import MACHINE_ID_FILE

pytestmark = pytest.mark.usefixtures("register_subman")


def assert_systemd_insights_client_timer_enabled_and_active():
    """
    Ensure the systemd timer for insights-client is enabled, active and scheduled.
    """
    result = subprocess.run(
        [
            "systemctl",
            "show",
            "insights-client.timer",
            "--property=UnitFileState,ActiveState,NextElapseUSecRealtime",
        ],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )

    systemd_timer_properties = dict(line.split("=", 1) for line in result.stdout.splitlines())

    # 1. enabled
    assert systemd_timer_properties["UnitFileState"] == "enabled"

    # 2. active
    assert systemd_timer_properties["ActiveState"] == "active"

    # 3. scheduled (systemd sometimes uses "infinity" when not scheduled)
    next_elapse = systemd_timer_properties["NextElapseUSecRealtime"]
    assert next_elapse and next_elapse != "infinity"


@pytest.mark.tier1
def test_register(insights_client):
    """
    :id: 5371018d-7b4a-4535-9bf9-7a7e60a9ee4a
    :title: Test client registration
    :description:
        This test verifies that the --register command successfully registers
        an unregistered client
    :tags: Tier 1
    :steps:
        1. Run insights-client with --register option
        2. Verify the client successfully registered
        3. Verify the report is successfully uploaded
        4. Verify the insights-client.timer is enabled and active
    :expectedresults:
        1. The client attempts to register
        2. The client is confirmed as registered and the output includes
            "Starting to collect Insights data."
        3. The output includes "Successfully uploaded report"
        4. The insights-client.timer is enabled and active
    """
    register_result = insights_client.run("--register")
    assert loop_until(lambda: insights_client.is_registered)

    assert "Starting to collect Insights data" in register_result.stdout
    assert "Successfully uploaded report" in register_result.stdout
    assert_systemd_insights_client_timer_enabled_and_active()


@pytest.mark.tier1
def test_register_auth_proxy(insights_client, test_config):
    """
    :id: 1387745b-59a1-4a90-8f6d-dee2afa4723c
    :title: Test registration with authenticated proxy
    :description:
        This test verifies that the --register command successfully registers the
        host when an authentication proxy is configured
    :tags: Tier 1
    :steps:
        1. Set the proxy configuration in the insights-client.conf file
        2. Run the insights-client with --register option and verbose output
        3. Verify the client is successfully registered
        4. Verify the insights-client.timer is enabled and active
    :expectedresults:
        1. The proxy details are saved to the client config file
        2. The client attempts to register, using the configured proxy
        3. The client is confirmed as registered and the output includes
            the proxy details (host,user) and 'Proxy Scheme'
        4. The insights-client.timer is enabled and active
    """
    try:
        proxy_host = test_config.get("auth_proxy", "host")
        proxy_user = test_config.get("auth_proxy", "username")
        proxy_pass = test_config.get("auth_proxy", "password")
        proxy_port = str(test_config.get("auth_proxy", "port"))
    except KeyError:
        pytest.skip("Skipping because this test needs proxy settings to be configured")

    auth_proxy = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"

    # save proxy information in insights-client.conf
    insights_client.config.proxy = auth_proxy
    insights_client.config.save()

    register_result = insights_client.run("--register", "--verbose")
    assert loop_until(lambda: insights_client.is_registered)
    assert "Proxy Scheme: http://" in register_result.stdout
    assert f"Proxy Location: {proxy_host}" in register_result.stdout
    assert f"Proxy User: {proxy_user}" in register_result.stdout
    assert_systemd_insights_client_timer_enabled_and_active()


@pytest.mark.tier1
def test_register_noauth_proxy(insights_client, test_config):
    """
    :id: cbde1ce7-97fc-48d4-85bb-955ca45c8862
    :title: Test registration with unauthenticated proxy
    :description:
        This test verifies that the --register command successfully registers the
        host when a unauthenticated proxy is configured
    :tags: Tier 1
    :steps:
        1. Set the proxy configuration in the insights-client.conf file
        2. Run the insights-client with --register option and verbose output
        3. Verify the client is successfully registered
        4. Verify the insights-client.timer is enabled and active
    :expectedresults:
        1. The proxy details are saved to the client config file
        2. The client attempts to register, using the configured proxy
        3. The client is confirmed as registered and the output includes
            'CONF Proxy' and the unauthenticated proxy details
        4. The insights-client.timer is enabled and active
    """
    try:
        proxy_host = test_config.get("noauth_proxy", "host")
        proxy_port = str(test_config.get("noauth_proxy", "port"))
    except KeyError:
        pytest.skip("Skipping because this test needs proxy settings to be configured")
    no_auth_proxy = f"http://{proxy_host}:{proxy_port}"
    insights_client.config.proxy = no_auth_proxy
    insights_client.config.save()

    register_result = insights_client.run("--register", "--verbose")
    assert loop_until(lambda: insights_client.is_registered)
    assert f"CONF Proxy: {no_auth_proxy}" in register_result.stdout
    assert_systemd_insights_client_timer_enabled_and_active()


@pytest.mark.tier1
def test_machineid_exists_only_when_registered(insights_client):
    """
    :id: 27440051-e0d3-452e-b052-070cddf65aa1
    :title: Test that machine ID file exists only when registered
    :description:
        This test verifies that the machine ID file is created only when the client
        is registered
    :tags: Tier 1
    :steps:
        1. Verify the client is not registered and machine ID does not exist
        2. Run the insights-client without registration
        3. Register insights-client and check machine ID
        4. Verify the insights-client.timer is enabled and active
        5. Unregister insights-client and confirm machine ID is removed
    :expectedresults:
        1. The client is not registered and machine ID does not exist
        2. The command fails with instructions to register in output and
            machine ID still does not exist
        3. Client is successfully registered and machine ID is present on the system
        4. The insights-client.timer is enabled and active
        5. The client is successfully unregistered and machine ID file is removed
    """
    assert loop_until(lambda: not insights_client.is_registered)
    assert not os.path.exists(MACHINE_ID_FILE)

    res = insights_client.run(check=False)
    assert (
        "This host is unregistered. Use --register to register this host" in res.stdout
        or "This host has not been registered. Use --register to register this host" in res.stdout
    )
    assert res.returncode != 0
    assert not os.path.exists(MACHINE_ID_FILE)

    insights_client.register()
    assert loop_until(lambda: insights_client.is_registered)
    assert os.path.exists(MACHINE_ID_FILE)
    assert_systemd_insights_client_timer_enabled_and_active()

    insights_client.unregister()
    assert not os.path.exists(MACHINE_ID_FILE)


@pytest.mark.tier1
def test_machineid_changes_on_new_registration(insights_client):
    """
    :id: ada04c6f-c351-4018-92f0-f3f21b7d645a
    :title: Test machine ID file changes on new registration
    :description:
        This test verifies that the machine ID file content changes when
        the client is unregistered and then registered again
    :tags: Tier 1
    :steps:
        1. Register insights-client and store current machine ID
        2. Verify the insights-client.timer is enabled and active
        3. Unregister the client
        4. Register client again and check the machine ID
        5. Verify the insights-client.timer is enabled and active
    :expectedresults:
        1. Client is registered and machine ID stored
        2. The insights-client.timer is enabled and active
        3. Client successfully unregisters and machine is removed
        4. After the registration on systems with version 3.3.16 and higher
            the machine ID should stay the same, on lower versions the number
            should change
        5. The insights-client.timer is enabled and active
    """
    insights_client.register()
    with open(MACHINE_ID_FILE, "r") as f:
        machine_id_old = f.read()
    assert_systemd_insights_client_timer_enabled_and_active()

    insights_client.unregister()
    assert not os.path.exists(MACHINE_ID_FILE)

    insights_client.register()
    with open(MACHINE_ID_FILE, "r") as f:
        machine_id_new = f.read()
    assert_systemd_insights_client_timer_enabled_and_active()

    if insights_client.core_version >= Version(3, 3, 16):
        """after the new changes to CCT-161 machine-id stays the same"""
        assert machine_id_new == machine_id_old
    else:
        assert machine_id_new != machine_id_old


@pytest.mark.tier1
def test_double_registration(insights_client):
    """
    :id: b1cf2516-aab9-438d-b4c0-42182c84fde9
    :title: Test double registration
    :description:
        This test verifies that the --register flag can be passed multiple
        times on a system that is already registered without causing errors
    :tags: Tier 1
    :steps:
        1. Register insights-client and store its machine ID
        2. Verify the insights-client.timer is enabled and active
        3. Run the --register command again on the registered system
        4. Verify the machine ID remains unchanged
        5. Verify the insights-client.timer is enabled and active
    :expectedresults:
        1. System is registered and machine ID is present
        2. The insights-client.timer is enabled and active
        3. The command does not fail and shows a message
            'This host has already been registered'
        4. The machine ID stayed unchanged
        5. The insights-client.timer is enabled and active
    """
    assert loop_until(lambda: not insights_client.is_registered)

    insights_client.register()
    assert os.path.exists(MACHINE_ID_FILE)
    with open(MACHINE_ID_FILE, "r") as f:
        machine_id_old = f.read()
    assert_systemd_insights_client_timer_enabled_and_active()

    res = insights_client.register()
    assert "This host has already been registered" in res.stdout
    assert os.path.exists(MACHINE_ID_FILE)
    with open(MACHINE_ID_FILE, "r") as f:
        machine_id_new = f.read()

    assert machine_id_new == machine_id_old
    assert_systemd_insights_client_timer_enabled_and_active()


@pytest.mark.parametrize(
    "legacy_upload_value",
    [
        pytest.param(True, marks=pytest.mark.xfail),
        pytest.param(False),
    ],
)
@pytest.mark.tier1
def test_register_group_option(insights_client, legacy_upload_value):
    """
    :id: 5213a950-e66f-4749-8a76-66b6d4ed9aa5
    :title: Test register with --group option
    :parametrized: yes
    :description:
        This test verifies that the --register command works as expected when
        --group option is used
    :reference: https://issues.redhat.com/browse/RHINENG-7567
    :tags: Tier 1
    :steps:
        1. Unregister the client if registered
        2. Set the legacy_upload value and save the configuration
        3. Run insights-client with --register and --group=tag options
        4. Verify the insights-client.timer is enabled and active
    :expectedresults:
        1. Client is unregistered successfully
        2. The configuration is updated successfully
        3. The client is registered with the specified group and the return
            code is 0
        4. The insights-client.timer is enabled and active
    """
    # make sure the system is not registered to insights
    with contextlib.suppress(Exception):
        insights_client.unregister()
    assert loop_until(lambda: not insights_client.is_registered)
    insights_client.config.legacy_upload = legacy_upload_value
    insights_client.config.save()
    register_group_option = insights_client.run(
        "--register",
        "--group=tag",
        check=False,
        selinux_context=None,  # using --group, not a service related option
    )
    assert register_group_option.returncode == 0
    assert_systemd_insights_client_timer_enabled_and_active()


@pytest.mark.tier1
def test_registered_and_unregistered_files_are_created_and_deleted(insights_client):
    """
    :id: 6e692793-f9ae-4ccb-a9d6-813b6d9aa7c3
    :title: Test files creation and deletion while registering and unregistering
    :description:
        This test verifies that the .registered file is created when the client
        is registered and the .unregistered file is created when the client is
        unregistered
    :tags: Tier 1
    :steps:
        1. Verify that the client is not registered and .registered file does not exist
        2. Register the client and verify that the .registered file was created
            and .unregistered does not appear
        3. Verify the insights-client.timer is enabled and active
        4. Unregister the client and verify that .registered file was removed and
            .unregistered file was created
    :expectedresults:
        1. Client is not registered and .registered file does not exist
        2. The client registers and .registered file is created, .unregistered
            does not exist
        3. The insights-client.timer is enabled and active
        4. The client is unregistered, .registered file was removed and .unregistered
            appears
    """
    assert loop_until(lambda: not insights_client.is_registered)
    assert not os.path.exists("/etc/insights-client/.registered")

    insights_client.register()
    assert loop_until(lambda: insights_client.is_registered)
    assert os.path.exists("/etc/insights-client/.registered")
    assert not os.path.exists("/etc/insights-client/.unregistered")
    assert_systemd_insights_client_timer_enabled_and_active()

    insights_client.unregister()
    assert os.path.exists("/etc/insights-client/.unregistered")
    assert not os.path.exists("/etc/insights-client/.registered")
