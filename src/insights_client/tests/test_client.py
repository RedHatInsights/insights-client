from unittest import mock
import insights_client
import pytest


# Test config load error
@mock.patch("os.getuid", return_value=0)
@mock.patch(
    "insights.client.InsightsConfig.load_all", side_effect=ValueError("mocked error")
)
def test_load_config_error(os_uid, insightsConfig):
    with pytest.raises(SystemExit) as sys_exit:
        insights_client._main()
    assert sys_exit.value.code != 0


# test keyboardinterrupt handler
@mock.patch("os.getuid", return_value=0)
@mock.patch("insights.client.InsightsConfig.load_all", side_effect=KeyboardInterrupt)
def test_keyboard_interrupt(os_uid, client):
    with pytest.raises(SystemExit) as sys_exit:
        insights_client._main()
    assert sys_exit.value.code != 0


# check run phase error 100 handler
@mock.patch("os.getuid", return_value=0)
@mock.patch("insights.client.phase.v1.get_phases")
@mock.patch("insights.client.InsightsClient")
@mock.patch("insights_client.subprocess.Popen")
def test_phase_error_100(mock_subprocess, client, phase, _os_getuid):
    client.get_conf = mock.Mock(return_value={"gpg": False})

    with pytest.raises(SystemExit) as sys_exit:
        mock_subprocess.return_value.returncode = 100
        mock_subprocess.return_value.communicate.return_value = ("output", "error")
        insights_client.run_phase(phase, client, validated_eggs=[])
    assert sys_exit.value.code == 0
