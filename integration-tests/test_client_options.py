import pytest
from time import sleep

pytestmark = pytest.mark.usefixtures("register_subman")


def test_set_ansible_host_info(insights_client):
    """
    Test if the ansible-host can be set with satellite
    Related to https://issues.redhat.com/browse/RHEL-3826
    """
    # Register system against Satellite, and register insights through satellite
    insights_client.register()
    sleep(10)
    assert insights_client.is_registered

    # Update ansible-host
    ret = insights_client.run("--ansible-host=foo.example.com", check=False)
    assert "Could not update Ansible hostname" not in ret.stdout
    assert ret.returncode == 0
