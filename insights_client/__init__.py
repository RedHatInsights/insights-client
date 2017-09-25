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
import logging
import logging.handlers

ENV_EGG = os.environ.get("EGG")
NEW_EGG = "/var/lib/insights/newest.egg"
STABLE_EGG = "/var/lib/insights/last_stable.egg"
RPM_EGG = "/etc/insights-client/rpm.egg"
EGGS = [ENV_EGG, NEW_EGG, STABLE_EGG, RPM_EGG]

logger = logging.getLogger(__name__)

sys.path = [STABLE_EGG, RPM_EGG] + sys.path

# handle user/group permissions
try:
    insights_uid = pwd.getpwnam("insights").pw_uid
    insights_gid = pwd.getpwnam("insights").pw_gid
    insights_grpid = grp.getgrnam("insights").gr_gid
    curr_user_grps = os.getgroups()
except:
    sys.exit("User and group 'insights' not found. Exiting.")


def log(msg):
    print(msg, file=sys.stderr)


def demote(uid, gid, phase):
    if os.geteuid() != 0:
        def result():
            os.setgid(gid)
            os.setuid(uid)
        return result


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
            log("Attempting %s with egg: %s" % (phase, egg))
        env = {
            "INSIGHTS_PHASE": str(phase),
            "PYTHONPATH": str(egg),
            "PATH": os.environ["PATH"]
        }
        process = subprocess.Popen(insights_command,
                                   preexec_fn=demote(insights_uid, insights_gid, phase),
                                   env=env)
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            # phase successful, don't try another egg
            break
        if process.returncode == 1:
            # egg hit an error, try the next
            logger.debug('Attempt failed.')
        if process.returncode >= 100:
            # 100 and 101 are unrecoverable, like post-unregistration, or
            #   a machine not being registered yet, or simply a 'dump & die'
            #   CLI option
            sys.exit(process.returncode % 100)


def _main():
    """
    attempt to update with current, fallback to rpm
    attempt to collect and upload with new, then current, then rpm
    if an egg fails a phase never try it again
    """

    # flake8 complains because these imports aren't at the top
    from insights.client import InsightsClient, get_phases  # noqa E402

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

    # check for insights user/group
    if not (insights_uid or insights_gid):
        log("WARNING: 'insights' user not found.  Using root to run all phases")

    # check if the user is in the insights group
    # make sure they are not root
    in_insights_group = insights_grpid in curr_user_grps
    if not in_insights_group and os.geteuid() != 0:
        log("ERROR: user not in 'insights' group AND not root. Exiting.")
        return

    for p in get_phases():
        run_phase(p, client)


if __name__ == '__main__':
    _main()
