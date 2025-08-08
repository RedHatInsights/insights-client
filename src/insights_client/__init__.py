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

try:
    from .constants import InsightsConstants
    from .constants import CORE_SELINUX_POLICY

    # if there is a policy for insights-core, unconditionally try to interface
    # with SELinux: insights-client was built with a policy for insights-core,
    # so not being able to apply that is an hard failure
    if CORE_SELINUX_POLICY != "":
        import selinux

        SWITCH_CORE_SELINUX_POLICY = selinux.is_selinux_enabled()
    else:
        SWITCH_CORE_SELINUX_POLICY = False
except ImportError:
    # The source file is build from 'constants.py.in' and is not
    # available during development
    class InsightsConstants(object):
        version = "development"

    CORE_SELINUX_POLICY = ""
    SWITCH_CORE_SELINUX_POLICY = False

LOG_FORMAT = "%(asctime)s %(levelname)8s %(name)s:%(lineno)s %(message)s"
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

# If we run as root, use the SELinux-safe temporary directory;
# otherwise, rely on the default temporary directory.
# This should be OK as the only operation doable as non-root is
# --version, and everything else already errors.
if os.geteuid() == 0:
    TEMPORARY_GPG_HOME_PARENT_DIRECTORY = "/var/lib/insights/"
else:
    TEMPORARY_GPG_HOME_PARENT_DIRECTORY = None


logger = logging.getLogger(__name__)


def get_logging_config():
    config = {}

    for arg in ["silent", "verbose"]:
        environ_variable = f"INSIGHTS_{arg.upper()}"
        environ_value = os.environ.get(environ_variable, "")

        if environ_value.lower() == "true":
            config[arg] = True
        else:
            cli_flag = f"--{arg}"
            config[arg] = cli_flag in sys.argv

    return config


def set_up_logging(logging_config):
    if logging_config["silent"]:
        logger.setLevel(logging.FATAL)
        return
    elif not logging_config["verbose"]:
        return

    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def tear_down_logging():
    for handler in logger.handlers:
        logger.removeHandler(handler)


def debug_environ(environ):
    items = map(lambda item: f"{item[0]}={item[1]}", environ.items())
    return " ".join(items)


def debug_command(command, environ=None):
    if environ:
        full_command = [debug_environ(environ)] + command
    else:
        full_command = command
    # Please note that neither spaces nor any other special characters are quoted.
    return " ".join(full_command)


def join_path(parts):
    return ":".join(parts)


def egg_version(egg):
    """
    Determine the egg version
    """
    if not sys.executable:
        return None
    try:
        version_command = [
            sys.executable,
            "-c",
            "from insights.client import InsightsClient; "
            "print(InsightsClient(None, False).version())",
        ]
        env = {"PYTHONPATH": egg, "PATH": os.getenv("PATH")}
        logger.debug("Running command: %s", debug_command(version_command, env))
        proc = Popen(version_command, env=env, stdout=PIPE, stderr=PIPE)
    except OSError:
        return None
    stdout, _stderr = proc.communicate()
    return stdout.decode("utf-8")


def egg_path(insights_module):
    module_path = insights_module.__path__[0]
    return os.path.dirname(module_path)


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
    shutdown_command = ["/usr/bin/gpgconf", "--homedir", home, "--kill", "all"]
    logger.debug("Running command: %s", " ".join(shutdown_command))
    shutdown_process = subprocess.Popen(
        shutdown_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env={"LC_ALL": "C.UTF-8"},
    )
    stdout, stderr = shutdown_process.communicate()
    if shutdown_process.returncode != 0:
        logger.debug(
            "Could not kill the GPG agent, got return code %d",
            shutdown_process.returncode,
        )
        if stdout:
            logger.debug("stdout: %s", stdout)
        if stderr:
            logger.debug("stderr: %s", stderr)

    # Delete the temporary directory
    logger.debug("Removing temporary directory: %s", home)
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
        logger.debug("Path '%s' does not exist and cannot be GPG validated.", path)
        return False

    # EGG may be a path to a directory (which cannot be signed)
    if BYPASS_GPG:
        logger.debug(
            "'BYPASS_GPG' is set, pretending the GPG validation of '%s' succeeded.",
            path,
        )
        return True

    if not os.path.exists(path + ".asc"):
        logger.debug("Path '%s' does not have an associated '.asc' file.", path)
        return False

    # The /var/lib/insights/ directory is used instead of /tmp/ because
    # GPG needs to have RW permissions in it, and existing SELinux rules only
    # allow access here.
    logger.debug(
        "Creating temporary directory in %s...", TEMPORARY_GPG_HOME_PARENT_DIRECTORY
    )
    home = tempfile.mkdtemp(dir=TEMPORARY_GPG_HOME_PARENT_DIRECTORY)

    # Import the public keys into temporary environment
    import_command = ["/usr/bin/gpg", "--homedir", home, "--import", GPG_KEY]
    logger.debug("Running command: %s", debug_command(import_command))
    import_process = subprocess.Popen(
        import_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"LC_ALL": "C.UTF-8"},
    )
    import_process.communicate()
    if import_process.returncode != 0:
        logger.debug(
            "Could not import the GPG key, got return code %d",
            import_process.returncode,
        )
        _remove_gpg_home(home)
        return False

    # Verify the signature
    verify_command = [
        "/usr/bin/gpg",
        "--homedir",
        home,
        "--verify",
        path + ".asc",
        path,
    ]
    logger.debug("Running command: %s", debug_command(verify_command))
    verify_process = subprocess.Popen(
        verify_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"LC_ALL": "C.UTF-8"},
    )
    verify_process.communicate()
    _remove_gpg_home(home)

    logger.debug(
        "The GPG verification of '%s' returned status code %d.",
        path,
        verify_process.returncode,
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
        logger.debug("Environment egg defined as %s." % ENV_EGG)

    for egg in all_eggs:
        if config["gpg"]:
            if not os.path.isfile(egg):
                logger.debug("%s is not a file, can't GPG verify. Skipping.", egg)
                continue
            if not client.verify(egg)["gpg"]:
                logger.debug("Not using egg: %s", egg)
                continue
        else:
            logger.debug("GPG disabled by --no-gpg, not verifying %s.", egg)

        logger.debug("phase '%s'; egg '%s'", phase["name"], egg)

        # prepare the environment
        pythonpath = str(egg)
        env_pythonpath = os.environ.get("PYTHONPATH", "")  # type: str
        if env_pythonpath:
            pythonpath = join_path([pythonpath, env_pythonpath])
        insights_env = {
            "INSIGHTS_PHASE": str(phase["name"]),
            "PYTHONPATH": pythonpath,
        }
        env = os.environ
        env.update(insights_env)

        if SWITCH_CORE_SELINUX_POLICY:
            # in case we can switch to a different SELinux policy for
            # insights-core, get the current context and switch the type
            context = selinux.context_new(selinux.getcon()[1])
            # additional check: in case the current type is a certain one
            # (e.g. unconfined_t when insights-client is run from a shell),
            # then the switch will not work
            source_type = selinux.context_type_get(context)
            if source_type not in ["unconfined_t", "sysadm_t"]:
                selinux.context_type_set(context, CORE_SELINUX_POLICY)
                new_core_context = selinux.context_str(context)
                selinux.setexeccon(new_core_context)
                logger.debug("Switched to SELinux context from {src} to {tgt}".format(
                    src=source_type,
                    tgt=CORE_SELINUX_POLICY,
                ))
            else:
                logger.debug("Staying in current SELinux context {src}".format(
                    src=source_type,
                ))
            selinux.context_free(context)
        process = subprocess.Popen(insights_command, env=env)
        process.communicate()
        if SWITCH_CORE_SELINUX_POLICY:
            # setexeccon() in theory ought to reset the context for the next
            # execv*() after that execution; it does not seem to happen though,
            # so for now manually reset it
            selinux.setexeccon(None)
            logger.debug(f"Switched out to original SELinux context")
        if process.returncode == 0:
            # phase successful, don't try another egg
            logger.debug("phase '%s' successful", phase["name"])
            update_motd_message()
            return

        if process.returncode not in [0, 100]:
            logger.debug(
                "phase '%s' failed with return code %d",
                phase["name"],
                process.returncode,
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
            "directory '%s' does not exist, ignoring MOTD update request",
            os.path.dirname(MOTD_FILE),
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
                "pointing the MOTD file '%s' to '%s'",
                MOTD_SRC,
                MOTD_FILE,
            )
            try:
                os.symlink(MOTD_SRC, MOTD_FILE)
            except OSError as exc:
                logger.debug(
                    "could not point the MOTD file '%s' to '%s': %s",
                    MOTD_SRC,
                    MOTD_FILE,
                    exc,
                )
        else:
            logger.debug(
                ".registered and .unregistered do not exist; "
                "file '%s' correctly points to '%s'",
                MOTD_SRC,
                MOTD_FILE,
            )

    else:
        # .registered or .unregistered exist, MOTD should not be displayed
        if os.path.lexists(MOTD_FILE):
            logger.debug(
                ".registered or .unregistered exist; removing the MOTD file '%s'",
                MOTD_FILE,
            )
            try:
                os.remove(MOTD_FILE)
            except OSError as exc:
                logger.debug("could not remove the MOTD file '%s': %s", MOTD_FILE, exc)
        else:
            logger.debug(
                ".registered or .unregistered exist; file '%s' correctly does "
                "not exist",
                MOTD_FILE,
            )


def _main():
    """
    attempt to update with current, fallback to rpm
    attempt to collect and upload with new, then current, then rpm
    if an egg fails a phase never try it again
    """
    logging_config = get_logging_config()
    set_up_logging(logging_config)

    if SWITCH_CORE_SELINUX_POLICY:
        logger.debug("Running with SELinux")
    else:
        logger.debug("Running without SELinux")

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
        print("Client: %s" % InsightsConstants.version)
        print("Core: not found")
        return

    # ENV egg comes first
    all_valid_eggs = valid_env_egg + validated_eggs
    logger.debug("Using eggs: %s", join_path(all_valid_eggs))
    sys.path = all_valid_eggs + sys.path

    try:
        # flake8 complains because these imports aren't at the top
        import insights

        logger.debug("Loaded initial egg: %s", egg_path(insights))

        from insights.client import InsightsClient
        from insights.client.phase.v1 import get_phases
        from insights.client.config import InsightsConfig

        # Add the insights-config here
        try:
            config = InsightsConfig(_print_errors=True, **logging_config).load_all()
        except ValueError as e:
            sys.stderr.write("ERROR: " + str(e) + "\n")
            sys.exit("Unable to load Insights Config")

        if config["version"]:
            print("Client: %s" % InsightsConstants.version)
            print("Core: %s" % InsightsClient().version())
            return

        if os.getuid() != 0:
            sys.exit("Insights client must be run as root.")

        # handle client instantiation here so that it isn't done multiple times
        # in __init__; the config can be passed now by parameter
        client = InsightsClient(config, False)  # read config, but dont setup logging
        logger.debug("InsightsClient initialized. Egg version: %s", client.version())

        # we now have access to the clients logging mechanism
        tear_down_logging()
        client.set_up_logging()

        for p in get_phases():
            run_phase(p, client, validated_eggs)
    except KeyboardInterrupt:
        sys.exit("Aborting.")


if __name__ == "__main__":
    _main()
