#!/usr/bin/python
"""
 Gather and upload Insights data for
 Red Hat Insights
"""
import os
import sys
import subprocess
from subprocess import PIPE

__author__ = 'Richard Brantley <rbrantle@redhat.com>, Jeremy Crafts <jcrafts@redhat.com>, Dan Varga <dvarga@redhat.com>'

EGGS = [
    "/var/lib/insights/newest.egg",
    "/var/lib/insights/last_stable.egg",
    "/etc/insights-client/rpm.egg"
]


def go(phase, eggs, inp=None):
    """
    Call the run script for the given phase.  If the phase succeeds returns the
    index of the egg that succeeded to be used in the next phase.
    """
    insights_command = ["insights-client-run"] + sys.argv[1:]
    for i, egg in enumerate(eggs):
        print("Attempting %s with %s" % (phase, egg))
        process = subprocess.Popen(insights_command, stdout=PIPE, stderr=PIPE, stdin=inp, env={
            "INSIGHTS_PHASE": str(phase),
            "PYTHONPATH": str(egg),
            "PATH": os.environ["PATH"]
        })
        stdout, stderr = process.communicate(inp)
        if stdout:
            print("%s stdout: %s" % (phase, stdout.strip()))
        if stderr:
            print("%s stderr: %s" % (phase, stderr.strip()))
        if process.wait() == 0:
            return stdout, i
    return None, None


def _main():
    """
    attempt to update with current, fallback to rpm
    attempt to collect and upload with new, then current, then rpm
    if an egg fails a phase never try it again
    """

    egg = os.environ.get("EGG")

    if not egg:
        go('update', EGGS[1:])

    eggs = [egg] if egg else EGGS
    response, i = go('collect', eggs)
    if response is not None:
        go('upload', eggs[i:], response)

if __name__ == '__main__':
    _main()
