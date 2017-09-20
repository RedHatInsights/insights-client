#!/usr/bin/python
"""
 Gather and upload Insights data for
 Red Hat Insights
"""
from __future__ import print_function
import json
import pwd
import grp
import os
import sys
import subprocess
import shutil
import logging
import logging.handlers
from subprocess import PIPE

# setup eggs
NEW_EGG = "/var/lib/insights/newest.egg"
STABLE_EGG = "/var/lib/insights/last_stable.egg"
RPM_EGG = "/etc/insights-client/rpm.egg"
EGGS = [NEW_EGG, STABLE_EGG, RPM_EGG]
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


def run_phase(client, phase, eggs, inp=None, process_response=True):
    """
    Call the run script for the given phase.  If the phase succeeds returns the
    index of the egg that succeeded to be used in the next phase.
    """
    insights_command = ["insights-client-run"] + sys.argv[1:]
    config = client.get_conf()
    debug = config["debug"]
    for i, egg in enumerate(eggs):
        if not os.path.isfile(egg):
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
                                   stdout=PIPE, stderr=PIPE, stdin=PIPE,
                                   env=env)
        # stdout is used to communicate with parent process
        # stderr is used to communicate with end user
        # return code indicates whether or not child process failed
        stdout, stderr = process.communicate(inp)
        if stderr:
            log(stderr.strip())
        if process.wait() == 0:
            response = process_stdout_response(config, stdout.strip(), process_response)
            if response is not False:
                return "" if response is True else response, i
        else:
            if debug:
                log("Attempt failed.")
    # All attempts to execute this phase have failed
    sys.exit(1)


def process_stdout_response(config, response, process_response):
    """
    Returns False if the phase execution was considered a failure, causing the
    phase to be be retried with a fallback egg if one is available.

    Returns the content in the "response" field is the execution was successful
    and the "response" field is not empty.  Otherwise it returns True (to
    indicate success).
    """
    if not process_response:
        return True
    try:
        d = json.loads(response)
        if d["message"] and not config['silent']:
            print(d["message"])
        if d["retry"]:
            return False
        elif d["rc"] is not None:
            sys.exit(d["rc"])
        else:
            return d["response"] if d["response"] else True
    except Exception as e:
        if config["debug"]:
            log("Failed to process subprocess output: %s", e.message)


def _main():
    """
    attempt to update with current, fallback to rpm
    attempt to collect and upload with new, then current, then rpm
    if an egg fails a phase never try it again
    """
    # flake8 complains because these imports aren't at the top
    from insights.client import InsightsClient  # noqa E402

    # handle client instantation here so that it isn't done multiple times in __init__
    client = InsightsClient(True, False)  # read config, but dont setup logging
    config = client.get_conf()

    # handle log rotation here instead of core
    if os.path.isfile(config['logging_file']):
        log_handler = logging.handlers.RotatingFileHandler(
            config['logging_file'], delay=True, backupCount=3)
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

    # get current egg environment
    egg = os.environ.get("EGG")

    r, _ = run_phase(client, 'pre_update', [STABLE_EGG, RPM_EGG])

    # if no egg was found, then get one
    if not egg:
        response, i = run_phase(client, 'update', EGGS[1:])

    eggs = [egg] if egg else EGGS
    r, _ = run_phase(client, 'post_update', eggs)

    # run collection
    response, i = run_phase(client, 'collect', eggs)
    if config["to_stdout"]:
        with open(response, 'rb') as f:
            shutil.copyfileobj(f, sys.stdout)
    elif response is not None:
        collection_response, collection_i = run_phase(client, 'upload', eggs[i:], response)


if __name__ == '__main__':
    _main()
