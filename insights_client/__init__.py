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
import shutil
from subprocess import PIPE

sys.path.insert(0, "/etc/insights-client/rpm.egg")
from insights.client import InsightsClient  # noqa E402
from insights.client import config  # noqa E402

__author__ = 'Richard Brantley <rbrantle@redhat.com>, Jeremy Crafts <jcrafts@redhat.com>, Dan Varga <dvarga@redhat.com>'

STDOUT_PREFIX = "STDOUTRESPONSE: "
RPM_EGG = "/etc/insights-client/rpm.egg"

EGGS = [
    "/var/lib/insights/newest.egg",
    "/var/lib/insights/last_stable.egg",
    RPM_EGG
]


client = InsightsClient()
debug = config["debug"]
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


def go(phase, eggs, inp=None):
    """
    Call the run script for the given phase.  If the phase succeeds returns the
    index of the egg that succeeded to be used in the next phase.
    """
    insights_command = ["insights-client-run"] + sys.argv[1:]
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
            return stdout, i
        else:
            if debug:
                log("Attempt failed.")
    return None, None


def process_stdout_response(response):
    """
    This is used to process any stdout/response from the client invocation
    This is an internally implemented protocol
    Any response from the client with STDOUT_PREFIX will be stripped/printed
    """
    if response and response.startswith(STDOUT_PREFIX):
        response_msg = response[len(STDOUT_PREFIX):].strip()
        if response_msg and not config['silent']:
            print(response_msg)
        return True


def _main():
    """
    attempt to update with current, fallback to rpm
    attempt to collect and upload with new, then current, then rpm
    if an egg fails a phase never try it again
    """

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

    # if no egg was found, then get one
    if not egg:
        response, i = go('update', EGGS[1:])
        if process_stdout_response(response):
            return

    # run collection
    eggs = [egg] if egg else EGGS
    response, i = go('collect', eggs)
    if config["to_stdout"]:
        with open(response.strip(), 'rb') as f:
            shutil.copyfileobj(f, sys.stdout)
        return
    if process_stdout_response(response):
        return

    # run upload
    if response is not None and response.strip() != "None":
        collection_response, collection_i = go('upload', eggs[i:], response)
        if process_stdout_response(collection_response):
            return


if __name__ == '__main__':
    _main()
