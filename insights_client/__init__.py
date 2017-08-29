#!/usr/bin/python
"""
 Gather and upload Insights data for
 Red Hat Insights
"""
import pwd
import grp
import os
import sys
import subprocess
from subprocess import PIPE

__author__ = 'Richard Brantley <rbrantle@redhat.com>, Jeremy Crafts <jcrafts@redhat.com>, Dan Varga <dvarga@redhat.com>'

STDOUT_PREFIX = "STDOUTRESPONSE: "
RPM_EGG = "/etc/insights-client/rpm.egg"

EGGS = [
    "/var/lib/insights/newest.egg",
    "/var/lib/insights/last_stable.egg",
    RPM_EGG
]

sys.path.insert(0, "/etc/insights-client/rpm.egg")

from insights.client import InsightsClient
from insights.client import config

client = InsightsClient()
debug = config["debug"]
try:
    insights_uid = pwd.getpwnam("insights").pw_uid
    insights_gid = pwd.getpwnam("insights").pw_gid
    insights_grpid = grp.getgrpname("insights").gr_gid
    insights_grpusers = grp.getgrpname("insights").gr_mem
    curr_user_grps = os.getgroups()
except:
    insights_uid, insights_gid = None, None
    insights_grpid, insights_grpusers = None, None
    curr_user_grps = os.getgroups()
    raise


def demote(uid, gid, phase):
    user_is_root = os.geteuid() is 0
    if uid and gid and phase != "collect" and not user_is_root:
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
                print("Egg does not exist: %s" % egg)
            continue
        if config['gpg'] and not client.verify(egg)['gpg']:
            print("WARNING: GPG verification failed.  Not loading egg: %s" % egg)
            continue
        if debug:
            print("Attempting %s with egg: %s" % (phase, egg))
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
            print(stderr.strip())
        if process.wait() == 0:
            return stdout, i
        else:
            if debug:
                print("Attempt failed.")
    return None, None


def process_stdout_response(response):
    """
    This is used to process any stdout/response from the client invocation
    This is an internally implemented protocol
    Any response from the client with STDOUT_PREFIX will be stripped/printed
    """
    if response and response.startswith(STDOUT_PREFIX):
        response_msg = response[len(STDOUT_PREFIX):].strip()
        if response_msg:
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
        print("WARNING: 'insights' user not found.  Using root to run all phases")

    # check if the user is in the insights group
    # make sure they are not root
    in_insights_group = insights_grpid in curr_user_grps
    is_root = os.geteuid() is 0
    if not in_insights_group and not is_root:
        print("ERROR: user not in 'insights' group AND not root. Exiting.")
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
    if process_stdout_response(response):
        return

    # run upload
    if response is not None and response.strip() != "None" and config["no_upload"] is not True:
        collection_response, collection_i = go('upload', eggs[i:], response)
        if process_stdout_response(collection_response):
            return


if __name__ == '__main__':
    _main()
