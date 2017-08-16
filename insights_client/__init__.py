#!/usr/bin/python
"""
 Gather and upload Insights data for
 Red Hat Insights
"""
import pwd
import os
import sys
import subprocess
from subprocess import PIPE

__author__ = 'Richard Brantley <rbrantle@redhat.com>, Jeremy Crafts <jcrafts@redhat.com>, Dan Varga <dvarga@redhat.com>'

INIT_PREFIX = "INIT: "
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
except:
    insights_uid, insights_gid = None, None
    raise


def demote(uid, gid, phase):
    if uid and gid and phase != "collect":
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


def process_init(response):
    if response and response.startswith(INIT_PREFIX):
        response_msg = response[len(INIT_PREFIX):].strip()
        if response_msg:
            print(response_msg)
        return True


def _main():
    """
    attempt to update with current, fallback to rpm
    attempt to collect and upload with new, then current, then rpm
    if an egg fails a phase never try it again
    """

    if not (insights_uid or insights_gid):
        print("WARNING: 'insights' user not found.  Using root to run all phases")

    egg = os.environ.get("EGG")

    if not egg:
        response, i = go('update', EGGS[1:])
        if process_init(response):
            return

    eggs = [egg] if egg else EGGS
    response, i = go('collect', eggs)
    if process_init(response):
        return
    if response is not None and response.strip() != "None" and config["no_upload"] is not True:
        go('upload', eggs[i:], response)


if __name__ == '__main__':
    _main()
