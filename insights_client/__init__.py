#!/usr/bin/python
"""
 Gather and upload Insights data for
 Red Hat Insights
"""
import sys
import subprocess

__author__ = 'Richard Brantley <rbrantle@redhat.com>, Jeremy Crafts <jcrafts@redhat.com>, Dan Varga <dvarga@redhat.com>'


def _main():
    """
    Main entry point

    Runs the client code up to two times.  The only reason we'd run two times
    is if we get a code update exit code on the first run.
    """

    # Instantiate Client API
    return_code = subprocess.call("insights-client-run")
    if return_code == 42:
        sys.exit(subprocess.call("insights-client-run"))
    else:
        sys.exit(return_code)


if __name__ == '__main__':
    _main()
