from unittest import mock
import insights_client
import pytest


# Test config load error
@mock.patch("os.getuid", return_value=0)
@mock.patch("insights_client.InsightsConfig")
def test_load_config_error(mock_config, os_uid):
    mock_config.return_value.load_all.side_effect = ValueError("mocked error")

    with pytest.raises(SystemExit) as sys_exit:
        insights_client._main()
    assert sys_exit.value.code != 0


# test keyboardinterrupt handler
@mock.patch("os.getuid", return_value=0)
@mock.patch("insights_client.InsightsConfig")
def test_keyboard_interrupt(mock_config, os_uid):
    mock_config.return_value.load_all.side_effect = KeyboardInterrupt()

    with pytest.raises(SystemExit) as sys_exit:
        insights_client._main()
    assert sys_exit.value.code != 0


# check run phase error 100 handler
@mock.patch("insights_client.subprocess.Popen")
def test_phase_error_100(mock_subprocess):
    mock_phase = {"name": "test_phase"}
    mock_client = mock.MagicMock()

    mock_subprocess.return_value.returncode = 100
    mock_subprocess.return_value.communicate.return_value = ("output", "error")

    with pytest.raises(SystemExit) as sys_exit:
        insights_client.run_phase(mock_phase, mock_client)
    assert sys_exit.value.code == 0


# Test version display
@mock.patch("os.getuid", return_value=0)
@mock.patch("insights_client.InsightsConfig")
@mock.patch("insights_client.InsightsClient")
@mock.patch("builtins.print")
def test_version_display(mock_print, mock_client_class, mock_config, os_uid):
    mock_config.return_value.load_all.return_value = {"version": True}
    mock_client_instance = mock.MagicMock()
    mock_client_instance.version.return_value = "test_core_version"
    mock_client_class.return_value = mock_client_instance

    insights_client._main()

    # Check that version info was printed
    assert mock_print.call_count == 2
    mock_print.assert_any_call("Client: %s" % insights_client.InsightsConstants.version)
    mock_print.assert_any_call("Core: test_core_version")


# Test non-root user
@mock.patch("os.getuid", return_value=1000)
@mock.patch("insights_client.InsightsConfig")
def test_non_root_user(mock_config, os_uid):
    mock_config.return_value.load_all.return_value = {"version": False}

    with pytest.raises(SystemExit) as sys_exit:
        insights_client._main()
    assert "root" in str(sys_exit.value)
