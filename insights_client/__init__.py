#!/usr/bin/python
"""
 Gather and upload Insights data for
 Red Hat Insights
"""
from __future__ import print_function
import pwd
import grp
import os
import sys
import subprocess
from subprocess import PIPE
import shlex
import logging
import logging.handlers

GPG_KEY = "/etc/insights-client/redhattools.pub.gpg"

BYPASS_GPG = os.environ.get("BYPASS_GPG", "").lower() == "true"
ENV_EGG = os.environ.get("EGG")
NEW_EGG = "/var/lib/insights/newest.egg"
STABLE_EGG = "/var/lib/insights/last_stable.egg"
RPM_EGG = "/etc/insights-client/rpm.egg"
EGGS = [ENV_EGG, NEW_EGG, STABLE_EGG, RPM_EGG]

logger = logging.getLogger(__name__)

# handle user/group permissions
try:
    insights_uid = pwd.getpwnam("insights").pw_uid
    insights_gid = pwd.getpwnam("insights").pw_gid
    insights_grpid = grp.getgrnam("insights").gr_gid
    curr_user_grps = os.getgroups()
except:
    insights_uid = insights_gid = insights_grpid = None


def log(msg):
    print(msg, file=sys.stderr)


def demote(uid, gid, run_as_root):
    if (run_as_root):
        return None
    if os.geteuid() == 0:
        def result():
            os.setgid(gid)
            os.setuid(uid)
        return result


def gpg_validate(path):
    if BYPASS_GPG:
        return True

    gpg_template = '/usr/bin/gpg --verify --keyring %s %s %s'
    cmd = gpg_template % (GPG_KEY, path + '.asc', path)
    proc = subprocess.Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
    proc.communicate()
    return proc.returncode == 0


def run_phase(phase, client):
    """
    Call the run script for the given phase.  If the phase succeeds returns the
    index of the egg that succeeded to be used in the next phase.
    """
    insights_command = ["insights-client-run"] + sys.argv[1:]
    config = client.get_conf()
    debug = config["debug"]
    for i, egg in enumerate(EGGS):
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
            "PYTHONPATH": str(egg),
            # get the binary name so we can use the appropriate conf dir for .registered files
            "INSIGHTS_SFR": sys.argv[0].rsplit('/', 1)[1]
        }
        env = os.environ
        env.update(insights_env)

        try:
            run_as_root = phase['run_as_root']
        except KeyError:
            run_as_root = False

        process = subprocess.Popen(insights_command,
                                   preexec_fn=demote(
                                       insights_uid, insights_gid, run_as_root),
                                   env=env)
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            # phase successful, don't try another egg
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


def _main():
    """
    attempt to update with current, fallback to rpm
    attempt to collect and upload with new, then current, then rpm
    if an egg fails a phase never try it again
    """

    if not all([insights_uid, insights_gid, insights_grpid]):
        sys.exit("User and/or group 'insights' not found. Exiting.")

    validated_eggs = filter(gpg_validate, [STABLE_EGG, RPM_EGG])

    if not validated_eggs:
        sys.exit("No GPG-verified eggs can be found")

    sys.path = validated_eggs + sys.path

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

        # check for insights user/group
        if not (insights_uid or insights_gid):
            log("WARNING: 'insights' user not found.  Using root to run all phases")

        # check if the user is in the insights group
        # make sure they are not root
        in_insights_group = insights_grpid in curr_user_grps
        if not in_insights_group and os.geteuid() != 0:
            log("ERROR: user not in 'insights' group AND not root. Exiting.")
            return

        if config["version"]:
            from insights_client.constants import InsightsConstants as constants
            print("Client: %s" % constants.version)
            print("Core: %s" % client.version())
            return

        for p in get_phases():
            run_phase(p, client)
    except KeyboardInterrupt:
        sys.exit('Aborting.')


if __name__ == '__main__':
    _main()
