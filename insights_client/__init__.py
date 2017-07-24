#!/usr/bin/python
"""
 Gather and upload Insights data for
 Red Hat Insights
"""
import sys
import subprocess

__author__ = 'Richard Brantley <rbrantle@redhat.com>, Jeremy Crafts <jcrafts@redhat.com>, Dan Varga <dvarga@redhat.com>'

EGGS = [
    "/var/lib/insights/newest.egg",
    "/var/lib/insights/last_stable.egg",
    "/etc/insights-client/rpm.egg"
]


def go(phase, eggs):
    """
    Call the run script for the given phase.  If the phase succeeds returns the
    index of the egg that succeeded to be used in the next phase.
    """
    insights_command = ["insights-client-run"] + sys.argv[1:]
    for idx, egg in enumerate(eggs):
        return_code = subprocess.call(insights_command, env={
            "INSIGHTS_PHASE": str(phase),
            "PYTHONPATH": str(egg)
        })
        if return_code == 0:
            return idx


def _main():
    """
    attempt to update with current, fallback to rpm
    attempt to collect and upload with new, then current, then rpm
    if an egg fails a phase never try it again
    """

    go('update', EGGS[1:])

    idx = go('collect', EGGS)
    if idx is not None:
        go('upload', EGGS[idx:])

if __name__ == '__main__':
    _main()
