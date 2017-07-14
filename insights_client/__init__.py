#!/usr/bin/python
"""
 Gather and upload Insights data for
 Red Hat Insights
"""
import os
import sys
from insights.client import run

__author__ = 'Richard Brantley <rbrantle@redhat.com>, Jeremy Crafts <jcrafts@redhat.com>, Dan Varga <dvarga@redhat.com>'


def _main():
    """
    Main entry point
    """

    # Require Root to run
    if os.geteuid() is not 0:
        sys.exit("Red Hat Insights must be run as root")

    # Instantiate Client API
    sys.exit(run())


if __name__ == '__main__':
    _main()
