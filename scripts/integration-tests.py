#!/usr/bin/env python3

import argparse
import itertools
import logging
import os
import pathlib
import shutil
import subprocess
import textwrap
import time
from typing import Optional


logging.basicConfig(
    level=logging.DEBUG,
    format="\033[34m{levelname:<7} {filename}:{lineno:>3}  {message}\033[0m",
    style="{",
)
logger = logging.getLogger(__name__)


IMAGE_NAME = "insights-client-test"
REPO_DIR = pathlib.Path(__file__).parent.parent
MISC_DIR = pathlib.Path("/tmp/insights-client-integration-tests/")
ARTIFACTS_DIR = MISC_DIR / "artifacts"
CONTAINERFILE_PATH = MISC_DIR / "Containerfile"
TEST_SETUP_SCRIPT_PATH = MISC_DIR / "test-setup.sh"
TEST_RUN_SCRIPT_PATH = MISC_DIR / "test-run.sh"
TEST_SCRIPT_PATH = MISC_DIR / "test.sh"

CONTAINERFILE = """
FROM quay.io/centos/centos:stream9 AS BUILD

RUN curl --silent https://copr.fedorainfracloud.org/coprs/g/yggdrasil/latest/repo/centos-stream-9/group_yggdrasil-latest-centos-stream-9.repo -o /etc/yum.repos.d/cct.repo \
&& dnf install --setopt install_weak_deps=False -y dnf-plugins-core \
&& dnf config-manager --set-enabled crb \
&& dnf install --setopt install_weak_deps=False -y epel-release \
&& dnf install --setopt install_weak_deps=False -y \
    meson cmake pkg-config \
    python3-requests python3-PyYAML python3-magic python3-six python3-setuptools \
    python3-pip git-core systemd \
    subscription-manager procps-ng \
    ncurses nano \
&& mkdir -p /etc/insights-client/ \
&& mkdir -p /var/log/insights-client/ \
&& mkdir -p /var/lib/insights/ \
&& mkdir -p /var/cache/insights/ \
&& mkdir -p /var/cache/insights-client/ \
&& export PYTHONDONTWRITEBYTECODE=1; echo "root:root" | chpasswd

CMD ["/sbin/init"]
"""

TEST_SETUP_SCRIPT = """
python3 -m pip install -r /client/integration-tests/requirements.txt
mkdir /build/
meson setup --prefix=/usr/ /build/ /client/
cd /build/
ninja install
cd /
"""

TEST_RUN_SCRIPT = """
python3 -m pytest --verbose --log-level debug -p no:cacheprovider /client/integration-tests/
"""

TEST_SCRIPT = """
bash /test-setup.sh
bash /test-run.sh
"""

SETTINGS_TOML = """[default]
candlepin.host = "subscription.rhsm.redhat.com"
candlepin.port = 443
candlepin.prefix = "/subscription"
candlepin.username = ""
candlepin.password = ""
insights.legacy_upload = false
"""

SCRIPTS: dict[pathlib.Path, str] = {
    TEST_SCRIPT_PATH: TEST_SCRIPT,
    TEST_SETUP_SCRIPT_PATH: TEST_SETUP_SCRIPT,
    TEST_RUN_SCRIPT_PATH: TEST_RUN_SCRIPT,
}


def setup() -> None:
    """Create temporary directory."""
    logger.info(f"Ensuring {MISC_DIR!s} exists")
    MISC_DIR.mkdir(exist_ok=True)
    ARTIFACTS_DIR.mkdir(exist_ok=True)


def cleanup() -> None:
    """Remove all temporary data."""
    logger.info(f"Removing {MISC_DIR!s}")
    shutil.rmtree(MISC_DIR, ignore_errors=True)


def build_image() -> None:
    """Build a Podman image prepared for tests."""
    logging.info("Building the container image")
    with CONTAINERFILE_PATH.open("w") as f:
        f.write(CONTAINERFILE)
    proc = subprocess.Popen(
        [
            "podman",
            "build",
            "-f",
            f"{CONTAINERFILE_PATH!s}",
            "-t",
            IMAGE_NAME,
        ],
    )
    proc.communicate()
    if proc.returncode == 0:
        logging.info(f"`podman build` returned code {proc.returncode}")
    else:
        logging.error(f"`podman build` returned code {proc.returncode}")
    logging.info(f"You can now run tests: `run --settings [FILE]`")


def _start_container(*, settings: pathlib.Path, egg: Optional[pathlib.Path]) -> str:
    """Start the container and return its ID."""
    logging.info("Starting the container")
    for script_path, script_content in SCRIPTS.items():
        with script_path.open("w") as f:
            f.write(script_content)
        os.chmod(script_path, 0o775)

    start_exec = ["podman", "run", "--rm", "-d", "--privileged"]
    hostname = ["--hostname", IMAGE_NAME]
    mounts = [
        f"{settings.absolute()!s}:/settings.toml:ro",
        f"{TEST_SETUP_SCRIPT_PATH!s}:/test-setup.sh:ro",
        f"{TEST_RUN_SCRIPT_PATH!s}:/test-run.sh:ro",
        f"{TEST_SCRIPT_PATH!s}:/test.sh:ro",
        f"{REPO_DIR!s}:/client/:ro",
        f"{ARTIFACTS_DIR!s}:/client/artifacts/:rw",
    ]
    egg_config = (
        []
        if egg is None
        else ["-v", f"{egg.absolute()!s}:/egg:ro", "-e", "EGG=/egg"]
    )
    start_command = [
        *start_exec,
        *hostname,
        *itertools.chain.from_iterable([["-v", mount] for mount in mounts]),
        *egg_config,
        f"localhost/{IMAGE_NAME}",
    ]

    logger.debug(" ".join(start_command))
    start_proc = subprocess.Popen(
        start_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    start_stdout, start_stderr = start_proc.communicate()

    if start_stderr:
        stderr = "\n".join(f"stderr: {line}" for line in start_stderr.split("\n"))
        logger.error(f"Error while starting the container\n{stderr}")
        raise RuntimeError

    logger.info("Waiting for systemd")
    time.sleep(5)

    return start_stdout.strip()


def _remove_container(container: str) -> None:
    logger.info(f"Tearing down container {container}")

    shutdown_exec = ["podman", "container", "rm", "-f"]
    shutdown_command = [*shutdown_exec, container]

    logger.debug(" ".join(shutdown_command))
    shutdown_proc = subprocess.Popen(
        shutdown_command, stdout=subprocess.PIPE, text=True
    )
    shutdown_proc.communicate()


def run_tests(*, settings: pathlib.Path, egg: Optional[pathlib.Path]) -> None:
    container = _start_container(settings=settings, egg=egg)

    run_exec = ["podman", "exec", "-it"]
    run_entrypoint = ["bash", "/test.sh"]
    run_command = [*run_exec, container, *run_entrypoint]

    logger.info("Running the tests")
    logger.debug(" ".join(run_command))
    run_proc = subprocess.Popen(run_command, text=True)
    run_proc.communicate()

    _remove_container(container)


def run_shell(*, settings: pathlib.Path, egg: Optional[pathlib.Path] = None) -> None:
    container = _start_container(settings=settings, egg=egg)

    run_exec = ["podman", "exec", "-it"]
    run_entrypoint = ["bash"]
    run_command = [*run_exec, container, *run_entrypoint]

    logger.info("Starting the shell")
    logger.debug(" ".join(run_command))
    logger.info("You can start the test manually: `/test.sh`")
    logger.info("To split setup and tests: `/test-setup.sh && /test-run.sh`")
    run_proc = subprocess.Popen(run_command, text=True)
    run_proc.communicate()

    _remove_container(container)


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
            Run the integration test suite for insights-client in a container:
            1/ install subscription-manager from team's COPR repository
            2/ install build and runtime dependencies
            3/ build insights-client from HEAD
            4/ run the integration tests
            """
        ),
    )

    subparser = parser.add_subparsers(
        dest="subcommand",
        description="valid actions",
    )
    subparser.add_parser(
        "generate-settings",
        help="generate settings.toml and exit",
    )
    subparser.add_parser(
        "build-image",
        help=f"build image `{IMAGE_NAME}`",
        epilog="Don't forget to run `podman image prune` from time to time :)",
    )

    parser_run_tests = subparser.add_parser("run", help=f"run integration tests")
    parser_run_tests.add_argument(
        "--settings", required=True, type=pathlib.Path, help="configuration file"
    )
    parser_run_tests.add_argument("--egg", type=pathlib.Path, help="custom egg file")

    parser_shell = subparser.add_parser("shell", help=f"inspect the container")
    parser_shell.add_argument(
        "--settings", required=True, type=pathlib.Path, help="configuration file"
    )
    parser_shell.add_argument("--egg", type=pathlib.Path, help="custom egg file")

    args = parser.parse_args()

    if args.subcommand is None:
        parser.print_help()
        return

    if args.subcommand == "generate-settings":
        print(SETTINGS_TOML.strip())
        return

    if args.subcommand == "build-image":
        setup()
        try:
            build_image()
            cleanup()
        except Exception:
            logger.exception(
                f"An error occurred. Directory {MISC_DIR} has been left dirty for inspection."
            )
        return

    if args.subcommand == "run":
        setup()
        try:
            run_tests(settings=args.settings, egg=args.egg)
            cleanup()
        except Exception:
            logger.exception(
                f"An error occurred. Directory {MISC_DIR} has been left dirty for inspection."
            )
        return

    if args.subcommand == "shell":
        setup()
        try:
            run_shell(settings=args.settings, egg=args.egg)
            cleanup()
        except Exception:
            logger.error(
                f"An error occurred. Directory {MISC_DIR} has been left dirty for inspection."
            )
        return


if __name__ == "__main__":
    main()
