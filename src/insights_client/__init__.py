"""
Gather and upload Insights data for Red Hat Insights
"""
import logging
import os
import subprocess
import sys

from insights.client import InsightsClient
from insights.client.phase.v1 import get_phases
from insights.client.config import InsightsConfig

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

MOTD_SRC = "/etc/insights-client/insights-client.motd"
MOTD_FILE = "/etc/motd.d/insights-client"
REGISTERED_FILE = "/etc/insights-client/.registered"
UNREGISTERED_FILE = "/etc/insights-client/.unregistered"


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


def run_phase(phase, client):
    """
    Call the run script for the given phase.
    """
    insights_command = [
        sys.executable,
        os.path.join(os.path.dirname(__file__), "run.py"),
    ] + sys.argv[1:]

    logger.debug("Running phase '%s'", phase["name"])

    # prepare the environment
    insights_env = {
        "INSIGHTS_PHASE": str(phase["name"]),
    }
    env = os.environ.copy()
    env.update(insights_env)

    if SWITCH_CORE_SELINUX_POLICY:
        # in case we can switch to a different SELinux policy for
        # insights-core, get the current context and switch the type
        context = selinux.context_new(selinux.getcon()[1])
        # additional check: in case the current type is a certain one
        # (e.g. unconfined_t when insights-client is run from a shell),
        # then the switch will not work
        if selinux.context_type_get(context) not in ["unconfined_t", "sysadm_t"]:
            selinux.context_type_set(context, CORE_SELINUX_POLICY)
            new_core_context = selinux.context_str(context)
            selinux.setexeccon(new_core_context)
        selinux.context_free(context)

    process = subprocess.Popen(insights_command, env=env)
    process.communicate()

    if SWITCH_CORE_SELINUX_POLICY:
        # setexeccon() in theory ought to reset the context for the next
        # execv*() after that execution; it does not seem to happen though,
        # so for now manually reset it
        selinux.setexeccon(None)

    if process.returncode == 0:
        # phase successful
        logger.debug("phase '%s' successful", phase["name"])
        update_motd_message()
        return

    if process.returncode not in [0, 100]:
        logger.debug(
            "phase '%s' failed with return code %d",
            phase["name"],
            process.returncode,
        )

    if process.returncode >= 100:
        # 100 and 101 are unrecoverable, like post-unregistration, or
        #   a machine not being registered yet, or simply a 'dump & die'
        #   CLI option
        #   * 100: Success, exit
        #   * 101: Failure, exit
        sys.exit(process.returncode % 100)

    # Phase failed
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
    Initialize and run insights client
    """
    logging_config = get_logging_config()
    set_up_logging(logging_config)

    try:
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

        client = InsightsClient(config, False)  # read config, but dont setup logging
        logger.debug("InsightsClient initialized. Version: %s", client.version())

        # we now have access to the clients logging mechanism
        tear_down_logging()
        client.set_up_logging()

        for p in get_phases():
            run_phase(p, client)
    except KeyboardInterrupt:
        sys.exit("Aborting.")


if __name__ == "__main__":
    _main()
