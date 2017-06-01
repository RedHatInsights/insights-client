#!/usr/bin/env python
import sys
import logging

from options import InsightsOptions
from constants import InsightsConstants as constants
from ansible_helper import InsightsAnsible
from core import InsightsCore

__author__ = 'Richard Brantley <rbrantle@redhat.com>'
LOG_FORMAT = ("%(asctime)s %(levelname)s %(message)s")
APP_NAME = 'insights-core'
logger = logging.getLogger(APP_NAME)

def main():
    '''
    Main entry point
    '''

    # Setup options
    the_options = InsightsOptions()
    options, args = the_options.parse_options_and_args()

    # Show version constant
    if options.show_version:
        print constants.version
        sys.exit(0)

    # setup the core
    mode = 'json'
    if options.returnarchive:
        mode = 'archive'
    if options.returnjson:
        mode = 'json'
    core = InsightsCore(mode, options)

    # are we utilizing ansible?
    ansible_helper = InsightsAnsible(core, options.inventory)
    has_ansible = ansible_helper.ansible_loaded
    if has_ansible and options.useansible:  # if its present and we are forcing ansible
        ansible_helper.run()
    elif has_ansible and options.dontuseansible == None:  # if it is present and we are not bypassing it (auto-detection)
        ansible_helper.run()
    else:
        core.run()


if __name__ == '__main__':
    '''
    Run the main entry point
    '''
    main()
