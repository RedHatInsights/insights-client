"""
 Gather and upload Insights data for
 Red Hat Insights
"""
from __future__ import print_function
import os
import sys
import six
import subprocess
from subprocess import Popen, PIPE
from distutils.version import LooseVersion
import shlex
import logging
import logging.handlers

GPG_KEY = "/etc/insights-client/redhattools.pub.gpg"

BYPASS_GPG = os.environ.get("BYPASS_GPG", "").lower() == "true"
ENV_EGG = os.environ.get("EGG")
NEW_EGG = "/var/lib/insights/newest.egg"
REGISTERED_FILE = "/etc/insights-client/.registered"
UNREGISTERED_FILE = "/etc/insights-client/.unregistered"
STABLE_EGG = "/var/lib/insights/last_stable.egg"
RPM_EGG = "/etc/insights-client/rpm.egg"
MOTD_FILE = "/etc/motd.d/insights-client"
MOTD_SRC = "/etc/insights-client/insights-client.motd"

logger = logging.getLogger(__name__)


def log(msg):
    print(msg, file=sys.stderr)


def egg_version(egg):
    '''
    Determine the egg version
    '''
    if not sys.executable:
        return None
    try:
        proc = Popen([sys.executable, '-c', 'from insights.client import InsightsClient; print(InsightsClient(None, False).version())'],
                     env={'PYTHONPATH': egg, 'PATH': os.getenv('PATH')}, stdout=PIPE, stderr=PIPE)
    except OSError:
        return None
    stdout, stderr = proc.communicate()
    if six.PY3:
        return stdout.decode('utf-8')
    else:
        return stdout


def sorted_eggs(eggs):
    '''
    Sort eggs to go into sys.path by highest version
    '''
    if len(eggs) < 2:
        # nothing to sort
        return eggs
    # default versions to 0 so LooseVersion doesn't throw a fit
    egg0_version = egg_version(eggs[0]) or '0'
    egg1_version = egg_version(eggs[1]) or '0'

    if LooseVersion(egg0_version) > LooseVersion(egg1_version):
        return eggs
    else:
        return [eggs[1], eggs[0]]


def gpg_validate(path):
    # ENV egg might be None, so check if path defined, then check if it exists
    if not (path and os.path.exists(path)):
        return False

    if BYPASS_GPG:
        return True

    if not os.path.exists(path + ".asc"):
        return False

    gpg_template = '/usr/bin/gpg --verify --keyring %s %s %s'
    cmd = gpg_template % (GPG_KEY, path + '.asc', path)
    proc = subprocess.Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
    proc.communicate()
    return proc.returncode == 0


def run_phase(phase, client, validated_eggs):
    """
    Call the run script for the given phase.  If the phase succeeds returns the
    index of the egg that succeeded to be used in the next phase.
    """
    insights_command = [sys.executable, os.path.join(os.path.dirname(__file__), "run.py")] + sys.argv[1:]
    config = client.get_conf()
    debug = config["debug"]

    all_eggs = [ENV_EGG, NEW_EGG] + validated_eggs

    for i, egg in enumerate(all_eggs):
        if egg is None or not os.path.isfile(egg):
            if debug:
                log("Egg does not exist: %s" % egg)
            continue
        if config['gpg'] and not client.verify(egg)['gpg']:
            log("WARNING: GPG verification failed.  Not loading egg: %s" % egg)
            continue
        if debug:
            log("Attempting %s with egg: %s" % (phase['name'], egg))

        # setup the env
        insights_env = {
            "INSIGHTS_PHASE": str(phase['name']),
            "PYTHONPATH": str(egg)
        }
        env = os.environ
        env.update(insights_env)

        process = subprocess.Popen(insights_command,
                                   env=env)
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            # phase successful, don't try another egg
            update_motd_message()
            return
        if process.returncode == 1:
            # egg hit an error, try the next
            logger.debug('Attempt failed.')
        if process.returncode >= 100:
            # 100 and 101 are unrecoverable, like post-unregistration, or
            #   a machine not being registered yet, or simply a 'dump & die'
            #   CLI option
            sys.exit(process.returncode % 100)
    # All attemps to run phase have failed
    sys.exit(1)


def update_motd_message():
    """
    motd displays a message about system not being registered. Once a
    registration stamp file exists, we make that message go away by pointing
    /etc/motd.d/insights-client at an empty file.

    It is intentional that the message does not reappear if a system is then
    unregistered. Only if both the unregistered and the registered stamp files
    do not exist is an motd symlink created.
    """
    try:
        if os.path.exists(os.path.dirname(MOTD_FILE)):
            if (os.path.isfile(REGISTERED_FILE) or os.path.isfile(UNREGISTERED_FILE)):
                os.symlink(os.devnull, MOTD_FILE + ".tmp")
                os.rename(MOTD_FILE + ".tmp", MOTD_FILE)
            else:
                os.symlink(MOTD_SRC, MOTD_FILE + ".tmp")
                os.rename(MOTD_FILE + ".tmp", MOTD_FILE)
    except OSError as e:
        # In the case of multiple processes
        logger.debug("Could not modify motd.d file: %s", str(e))


def _main():
    """
    attempt to update with current, fallback to rpm
    attempt to collect and upload with new, then current, then rpm
    if an egg fails a phase never try it again
    """
    # sort rpm and stable eggs after verification
    validated_eggs = sorted_eggs(
        list(filter(gpg_validate, [STABLE_EGG, RPM_EGG])))
    # if ENV_EGG was specified and it's valid, add that to front of sys.path
    #  so it can be loaded initially. keep it in its own var so we don't
    #  pass it to run_phase where we load it again
    if gpg_validate(ENV_EGG):
        valid_env_egg = [ENV_EGG]
    else:
        valid_env_egg = []

    if not validated_eggs and not valid_env_egg:
        sys.exit("No GPG-verified eggs can be found")

    # ENV egg comes first
    sys.path = valid_env_egg + validated_eggs + sys.path

    try:
        # flake8 complains because these imports aren't at the top
        import insights
        from insights.client import InsightsClient
        from insights.client.phase.v1 import get_phases

        # handle client instantation here so that it isn't done multiple times in __init__
        client = InsightsClient(True, False)  # read config, but dont setup logging
        config = client.get_conf()

        # handle log rotation here instead of core
        if os.path.isfile(config['logging_file']):
            log_handler = logging.handlers.RotatingFileHandler(
                config['logging_file'], backupCount=3)
            log_handler.doRollover()
        # we now have access to the clients logging mechanism instead of using print
        client.set_up_logging()
        logging.root.debug("Loaded initial egg: %s", os.path.dirname(insights.__file__))

        if config["version"]:
            from insights_client.constants import InsightsConstants as constants
            print("Client: %s" % constants.version)
            print("Core: %s" % client.version())
            return

        for p in get_phases():
            run_phase(p, client, validated_eggs)
    except KeyboardInterrupt:
        sys.exit('Aborting.')


if __name__ == '__main__':
    _main()
