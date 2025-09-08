# -*- coding: utf-8 -*-

import insights_client
from unittest.mock import patch
from pytest import raises


@patch("insights_client.sys.argv", ["insights-client", "--version"])
@patch("insights_client._main")
def test_version_command(capsys):
    with patch("os.getuid", return_value=0):
        insights_client._main()
        captured = capsys.readouterr()
        output_sudo = captured.out
    with patch("os.getuid", return_value=1):
        insights_client._main()
        captured = capsys.readouterr()
        output_normal = captured.out

    assert output_sudo == output_normal


@patch("insights_client.sys.argv", ["insights-client", "--help"])
@patch("insights_client._main")
def test_help_command(capsys):
    with patch("os.getuid", return_value=0):
        insights_client._main()
        captured = capsys.readouterr()
        output_sudo = captured.out
    with patch("os.getuid", return_value=1):
        insights_client._main()
        captured = capsys.readouterr()
        output_normal = captured.out

    assert output_sudo == output_normal


@patch("insights_client.sys.argv", ["insights-client"])
@patch("insights_client.InsightsConfig")
def test_exit_when_run_phases_no_sudo(mock_config):
    # Mock config to return version=False so it doesn't exit early
    mock_config.return_value.load_all.return_value = {"version": False}

    with raises(SystemExit) as pytest_wrapped_e:
        with patch("os.getuid", return_value=1):
            insights_client._main()
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.args[0] == "Insights client must be run as root."
