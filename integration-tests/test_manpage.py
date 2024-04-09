import gzip
import pytest


@pytest.mark.parametrize(
    "option",
    [
        "--checkin",
        "--compliance",
        "--conf",
        "--content-type",
        "--diagnosis",
        "--disable-schedule",
        "--display-name",
        "--enable-schedule",
        "--group",
        "--keep-archive",
        "--list-specs",
        "--logging-file",
        "--net-debug",
        "--no-upload",
        "--offline",
        "--output-dir",
        "--output-file",
        "--payload",
        "--quiet",
        "--register",
        "--retry",
        "--show-results",
        "--silent",
        "--status",
        "--test-connection",
        "--unregister",
        "--validate",
        "--verbose",
        "--version",
    ],
)
def test_manpage(option):
    """Test insights-client man page entries"""
    file = "/usr/share/man/man8/insights-client.8.gz"
    opened_file = gzip.open(file, "rt")
    content = opened_file.read()
    assert option in content, f"Option {option} is not present"
