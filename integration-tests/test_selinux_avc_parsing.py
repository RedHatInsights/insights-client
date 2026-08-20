"""Unit-level coverage for SELinuxAVCChecker.get_avcs() aureport parsing.

Does not require a live SELinux-enabled system: subprocess.run is mocked.
Covers the two aureport header shapes seen across supported RHEL versions
(see CCT-2793).
"""

from unittest.mock import MagicMock, patch

import pytest

from selinux import SELinuxAVCChecker

_AVC_ROW = (
    "1. 08/13/2026 10:00:00 insights-client "
    "system_u:system_r:insights_client_t:s0 openat file read "
    "unconfined_u:object_r:admin_home_t:s0 denied 123"
)

# RHEL <= 10.1: leading blank line before "AVC Report"
LEGACY_AUREPORT = f"""
AVC Report
===============================================================
# date time comm subj syscall class permission obj result event
===============================================================
{_AVC_ROW}
===============================================================
"""

# RHEL >= 10.2: no leading blank line
RHEL10_AUREPORT = f"""AVC Report
===============================================================
# date time comm subj syscall class permission obj result event
===============================================================
{_AVC_ROW}
===============================================================
"""

NO_EVENTS_AUREPORT = """
AVC Report
===============================================================
# date time comm subj syscall class permission obj result event
===============================================================
<no events of interest were found>
===============================================================
"""


def _mock_run(output: str, returncode: int = 0, stderr: str = ""):
    mock_result = MagicMock()
    mock_result.stdout = output.encode()
    mock_result.stderr = stderr.encode()
    mock_result.returncode = returncode
    return mock_result


def test_get_avcs_parses_legacy_header_format():
    with patch("selinux.subprocess.run", return_value=_mock_run(LEGACY_AUREPORT)):
        with SELinuxAVCChecker() as checker:
            entries = list(checker.get_avcs(skiplisted=False))
    assert len(entries) == 1
    assert entries[0]["comm"] == "insights-client"


def test_get_avcs_parses_rhel10_header_format_no_leading_blank_line():
    with patch("selinux.subprocess.run", return_value=_mock_run(RHEL10_AUREPORT)):
        with SELinuxAVCChecker() as checker:
            entries = list(checker.get_avcs(skiplisted=False))
    assert len(entries) == 1
    assert entries[0]["comm"] == "insights-client"


@pytest.mark.parametrize(
    "output",
    [NO_EVENTS_AUREPORT, NO_EVENTS_AUREPORT.lstrip("\n")],
    ids=["leading-blank-line", "no-leading-blank-line"],
)
def test_get_avcs_no_events_returns_empty(output):
    with patch("selinux.subprocess.run", return_value=_mock_run(output)):
        with SELinuxAVCChecker() as checker:
            assert list(checker.get_avcs(skiplisted=False)) == []


def test_get_avcs_raises_on_aureport_failure():
    with patch(
        "selinux.subprocess.run",
        return_value=_mock_run("", returncode=1, stderr="aureport: command not found"),
    ):
        with SELinuxAVCChecker() as checker:
            with pytest.raises(RuntimeError, match="aureport failed"):
                list(checker.get_avcs(skiplisted=False))


def test_get_avcs_no_events_with_nonzero_exit_does_not_raise():
    # aureport documents exit code 1 as ambiguous: it means either "nothing
    # found" or a minor argument/file error. A clean "nothing found" run
    # leaves stderr empty, so this must NOT be treated as a failure.
    with patch(
        "selinux.subprocess.run",
        return_value=_mock_run(NO_EVENTS_AUREPORT, returncode=1, stderr=""),
    ):
        with SELinuxAVCChecker() as checker:
            assert list(checker.get_avcs(skiplisted=False)) == []


def test_get_avcs_raises_on_unrecognized_output_format():
    # Non-empty, not the "no events" case, but the header/separator pattern
    # we know how to parse isn't there -- e.g. a future aureport format
    # change. Must raise rather than silently reporting "no AVCs", since we
    # genuinely don't know whether events are present in this output.
    with patch(
        "selinux.subprocess.run",
        return_value=_mock_run("Some unexpected report layout\nwith no separators at all\n"),
    ):
        with SELinuxAVCChecker() as checker:
            with pytest.raises(RuntimeError, match="unrecognized aureport output format"):
                list(checker.get_avcs(skiplisted=False))


def test_get_avcs_respects_skiplist():
    with patch("selinux.subprocess.run", return_value=_mock_run(RHEL10_AUREPORT)):
        with SELinuxAVCChecker() as checker:
            checker.skip_avc_entry_by_fields({"comm": "insights-client"})
            assert list(checker.get_avcs(skiplisted=True)) == []
