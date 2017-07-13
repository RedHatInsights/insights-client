#!/usr/bin/python
"""
 Gather and upload Insights data for
 Red Hat Insights
"""
import os
import sys
import logging
from constants import InsightsConstants as constants

__author__ = 'Richard Brantley <rbrantle@redhat.com>, Jeremy Crafts <jcrafts@redhat.com>, Dan Varga <dvarga@redhat.com>'

LOG_FORMAT = ("%(asctime)s %(levelname)s %(message)s")
APP_NAME = constants.app_name
logger = logging.getLogger(APP_NAME)

def _main():
    """
    Main entry point
    """
    if os.geteuid() is not 0:
        sys.exit("Red Hat Insights must be run as root")

    print "Running Inights Client"
    sys.exit(0)

if __name__ == '__main__':
    _main()
