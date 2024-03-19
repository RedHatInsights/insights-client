"""
 Gather and upload Insights data for
 Red Hat Insights
"""

from __future__ import print_function

import logging
import os
import shutil
import subprocess
from subprocess import Popen, PIPE
import sys
import tempfile

from distutils.version import LooseVersion


INSIGHTS_DEBUG = os.environ.get("INSIGHTS_DEBUG", "").lower() == "true"
NO_COLOR = os.environ.get("NO_COLOR") is not None

BYPASS_GPG = os.environ.get("BYPASS_GPG", "").lower() == "true"
GPG_KEY = "/etc/insights-client/redhattools.pub.gpg"

ENV_EGG = os.environ.get("EGG")
NEW_EGG = "/var/lib/insights/newest.egg"
STABLE_EGG = "/var/lib/insights/last_stable.egg"
RPM_EGG = "/etc/insights-client/rpm.egg"

MOTD_SRC = "/etc/insights-client/insights-client.motd"
MOTD_FILE = "/etc/motd.d/insights-client"
REGISTERED_FILE = "/etc/insights-client/.registered"
UNREGISTERED_FILE = "/etc/insights-client/.unregistered"

TEMPORARY_GPG_HOME_PARENT_DIRECTORY = "/var/lib/insights/"


logger = logging.getLogger(__name__)


def client_debug(message):
    """Debug a log message when logging isn't available yet.

    Set 'INSIGHTS_DEBUG' variable to enable this method.

    :param message: Text to display
    :type message: str
    """
    if not INSIGHTS_DEBUG:
        return

    prefix = "insights-client debug"
    suffix = ""
    if NO_COLOR or not sys.stdout.isatty():
        prefix += ":"
    else:
        prefix = "\033[40m" + prefix + "\033[0m\033[33m"
        suffix = "\033[0m"

    print(prefix + " " + message + suffix, file=sys.stderr)


def log(msg):
    print(msg, file=sys.stderr)


def egg_version(egg):
    """
    Determine the egg version
    """
    if not sys.executable:
        return None
    try:
        proc = Popen(
            [
                sys.executable,
                "-c",
                "from insights.client import InsightsClient; print(InsightsClient(None, False).version())",
            ],
            env={"PYTHONPATH": egg, "PATH": os.getenv("PATH")},
            stdout=PIPE,
            stderr=PIPE,
        )
    except OSError:
        return None
    stdout, stderr = proc.communicate()
    return stdout.decode("utf-8")


def sorted_eggs(eggs):
    """
    Sort eggs to go into sys.path by highest version
    """
    if len(eggs) < 2:
        # nothing to sort
        return eggs
    # default versions to 0 so LooseVersion doesn't throw a fit
    egg0_version = egg_version(eggs[0]) or "0"
    egg1_version = egg_version(eggs[1]) or "0"

    if LooseVersion(egg0_version) > LooseVersion(egg1_version):
        return eggs
    else:
        return [eggs[1], eggs[0]]


def _remove_gpg_home(home):
    """Clean GPG's temporary home directory at path 'home'.

    :param home: Path to the GPG's temporary home.
    :type home: str
    :rtype: None
    """
    # Shut down GPG's home agent
    shutdown_process = subprocess.Popen(
        ["/usr/bin/gpgconf", "--homedir", home, "--kill", "all"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    stdout, stderr = shutdown_process.communicate()
    if shutdown_process.returncode != 0:
        log(
            "Could not kill the GPG agent, got return code {rc}".format(
                rc=shutdown_process.returncode
            )
        )
        if stdout:
            log(stdout)
        if stderr:
            log(stderr)

    # Delete the temporary directory
    shutil.rmtree(home)


def gpg_validate(path):
    """Verify an egg at given path has valid GPG signature.

    This is an abridged version of GPG verification that is present in
    egg's client/crypto.py.

    :param path: Path to the egg file.
    :type path: str

    :returns: `True` if the GPG signature matches, `False` otherwise.
    """
    # EGG= may be None or an invalid path
    if not path or not os.path.exists(path):
        client_debug(
            "Path '{path}' does not exist and cannot be GPG validated.".format(
                path=path
            )
        )
        return False

    # EGG may be a path to a directory (which cannot be signed)
    if BYPASS_GPG:
        client_debug(
            "'BYPASS_GPG' is set, pretending the GPG validation of '{path}' succeeded.".format(
                path=path
            )
        )
        return True

    if not os.path.exists(path + ".asc"):
        client_debug(
            "Path '{path}' does not have an associated '.asc' file.".format(path=path)
        )
        return False

    # The /var/lib/insights/ directory is used instead of /tmp/ because
    # GPG needs to have RW permissions in it, and existing SELinux rules only
    # allow access here.
    home = tempfile.mkdtemp(dir=TEMPORARY_GPG_HOME_PARENT_DIRECTORY)

    # Import the public keys into temporary environment
    import_process = subprocess.Popen(
        ["/usr/bin/gpg", "--homedir", home, "--import", GPG_KEY],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    import_process.communicate()
    if import_process.returncode != 0:
        _remove_gpg_home(home)
        return False

    # Verify the signature
    verify_process = subprocess.Popen(
        ["/usr/bin/gpg", "--homedir", home, "--verify", path + ".asc", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    verify_process.communicate()
    _remove_gpg_home(home)

    client_debug(
        "The GPG verification of '{path}' returned status code {code}.".format(
            path=path,
            code=verify_process.returncode,
        )
    )
    return verify_process.returncode == 0


def run_phase(phase, client, validated_eggs):
    """
    Call the run script for the given phase.  If the phase succeeds returns the
    index of the egg that succeeded to be used in the next phase.
    """
    insights_command = [
        sys.executable,
        os.path.join(os.path.dirname(__file__), "run.py"),
    ] + sys.argv[1:]
    config = client.get_conf()

    all_eggs = [NEW_EGG] + validated_eggs
    if ENV_EGG is not None:
        all_eggs = [ENV_EGG] + all_eggs
        client_debug("Environment egg defined as %s." % ENV_EGG)

    for egg in all_eggs:
        if config["gpg"]:
            if not os.path.isfile(egg):
                client_debug("%s is not a file, can't GPG verify. Skipping." % (egg,))
                continue
            client_debug("Verifying %s..." % egg)
            if not client.verify(egg)["gpg"]:
                client_debug(
                    "WARNING: GPG verification failed. Not loading egg: %s" % egg
                )
                continue
        else:
            client_debug("GPG disabled by --no-gpg, not verifying %s." % egg)

        client_debug("phase '%s'; egg '%s'" % (phase["name"], egg))

        # prepare the environment
        pythonpath = str(egg)
        env_pythonpath = os.environ.get("PYTHONPATH", "")  # type: str
        if env_pythonpath:
            pythonpath += ":" + env_pythonpath
        insights_env = {
            "INSIGHTS_PHASE": str(phase["name"]),
            "PYTHONPATH": pythonpath,
        }
        env = os.environ
        env.update(insights_env)

        process = subprocess.Popen(insights_command, env=env)
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            # phase successful, don't try another egg
            client_debug("phase '{phase}' successful".format(phase=phase["name"]))
            update_motd_message()
            return

        client_debug(
            "phase '{phase}' failed with return code {rc}".format(
                phase=phase["name"], rc=process.returncode
            )
        )
        if process.returncode == 1:
            # egg hit an error, try the next
            logger.debug("Attempt failed.")
        if process.returncode >= 100:
            # 100 and 101 are unrecoverable, like post-unregistration, or
            #   a machine not being registered yet, or simply a 'dump & die'
            #   CLI option
            #   * 100: Success, exit
            #   * 101: Failure, exit
            sys.exit(process.returncode % 100)

    # All attempts to run phase have failed
    sys.exit(1)


def update_motd_message():
    """Update MOTD (after a phase was run).

    MOTD displays a message about system not being registered. Once a
    registration stamp file exists, we make that message go away by pointing
    /etc/motd.d/insights-client at an empty file.

    It is intentional that the message does not reappear if a system is then
    unregistered. Only if both the unregistered and the registered stamp files
    do not exist is a motd symlink created.

    The motd message could also be deliberately disabled by the users before
    registration, simply because they don't want to use insights-client, by
    pointing /etc/motd.d/insights-client at an empty file.
    """
    if not os.path.exists(os.path.dirname(MOTD_FILE)):
        logger.debug(
            "directory '{dir}' does not exist, ignoring MOTD update request".format(
                dir=os.path.dirname(MOTD_FILE)
            )
        )
        return

    if os.path.exists(MOTD_FILE) and os.path.samefile(os.devnull, MOTD_FILE):
        logger.debug("MOTD file points at /dev/null, ignoring MOTD update request")
        return

    motd_should_exist = not os.path.exists(REGISTERED_FILE) and not os.path.exists(
        UNREGISTERED_FILE
    )

    if motd_should_exist:
        # .registered & .unregistered do not exist, MOTD should be displayed
        if not os.path.lexists(MOTD_FILE):
            logger.debug(
                ".registered and .unregistered do not exist; "
                "pointing the MOTD file '{source}' to '{motd}'".format(
                    source=MOTD_SRC, motd=MOTD_FILE
                )
            )
            try:
                os.symlink(MOTD_SRC, MOTD_FILE)
            except OSError as exc:
                logger.debug(
                    "could not point the MOTD file '{source}' to '{motd}': {exc}".format(
                        source=MOTD_SRC, motd=MOTD_FILE, exc=exc
                    )
                )
        else:
            logger.debug(
                ".registered and .unregistered do not exist; "
                "file '{source}' correctly points to '{motd}'".format(
                    source=MOTD_SRC, motd=MOTD_FILE
                )
            )

    else:
        # .registered or .unregistered exist, MOTD should not be displayed
        if os.path.lexists(MOTD_FILE):
            logger.debug(
                ".registered or .unregistered exist; removing the MOTD file '{path}'".format(
                    path=MOTD_FILE
                )
            )
            try:
                os.remove(MOTD_FILE)
            except OSError as exc:
                logger.debug(
                    "could not remove the MOTD file '{path}': {exc}".format(
                        path=MOTD_FILE, exc=exc
                    )
                )
        else:
            logger.debug(
                ".registered or .unregistered exist; file '{motd}' correctly does not exist".format(
                    motd=MOTD_FILE
                )
            )


def _main():
    """
    attempt to update with current, fallback to rpm
    attempt to collect and upload with new, then current, then rpm
    if an egg fails a phase never try it again
    """

    # sort rpm and stable eggs after verification
    validated_eggs = sorted_eggs(list(filter(gpg_validate, [STABLE_EGG, RPM_EGG])))
    # if ENV_EGG was specified and it's valid, add that to front of sys.path
    #  so it can be loaded initially. keep it in its own var so we don't
    #  pass it to run_phase where we load it again
    if gpg_validate(ENV_EGG):
        valid_env_egg = [ENV_EGG]
    else:
        valid_env_egg = []

    if not validated_eggs and not valid_env_egg:
        sys.exit("No GPG-verified initial eggs can be found")

    # ENV egg comes first
    all_valid_eggs = valid_env_egg + validated_eggs
    client_debug("Using eggs: %s", ":".join(all_valid_eggs))
    sys.path = all_valid_eggs + sys.path

    try:
        # flake8 complains because these imports aren't at the top
        import insights
        from insights.client import InsightsClient
        from insights.client.phase.v1 import get_phases
        from insights.client.config import InsightsConfig

        # Add the insights-config here
        try:
            config = InsightsConfig(_print_errors=True).load_all()
        except ValueError as e:
            sys.stderr.write("ERROR: " + str(e) + "\n")
            sys.exit("Unable to load Insights Config")

        if config["version"]:
            try:
                from insights_client.constants import InsightsConstants
            except ImportError:
                # The source file is build from 'constants.py.in' and is not available during development
                class InsightsConstants(object):
                    version = "development"

            print("Client: %s" % InsightsConstants.version)
            print("Core: %s" % InsightsClient().version())
            return

        if os.getuid() != 0:
            sys.exit("Insights client must be run as root.")

        # handle client instantation here so that it isn't done multiple times in __init__
        # The config can be passed now by parameter
        client = InsightsClient(config, False)  # read config, but dont setup logging

        # we now have access to the clients logging mechanism instead of using print
        client.set_up_logging()
        logging.root.debug("Loaded initial egg: %s", os.path.dirname(insights.__file__))

        for p in get_phases():
            run_phase(p, client, validated_eggs)
    except KeyboardInterrupt:
        sys.exit("Aborting.")


if __name__ == "__main__":
    _main()
