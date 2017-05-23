#!/usr/bin/env python
import sys
import logging
import optparse

__author__ = 'Richard Brantley <rbrantle@redhat.com>'
LOG_FORMAT = ("%(asctime)s %(levelname)s %(message)s")
APP_NAME = 'insights-core'
logger = logging.getLogger(APP_NAME)

def main():
    '''
    Main entry point
    '''

    parser = optparse.OptionParser()
    parser.add_option('--version','-v',
                      help="Display version",
                      action="store_true",
                      dest="show_version",
                      default=False)
    parser.add_option('--verbose','-V',
                      help="Run verbosely",
                      action="store_true",
                      dest="verbose",
                      default=False)
    parser.add_option('--nogpg','-G',
                      help=optparse.SUPPRESS_HELP,
                      action="store_true",
                      dest="nogpg",
                      default=False)
    parser.add_option('--devmode','-d',
                      help=optparse.SUPPRESS_HELP,
                      action="store_true",
                      dest="devmode",
                      default=False)
    parser.add_option('--usegit','-g',
                      help=optparse.SUPPRESS_HELP,
                      action="store_true",
                      dest="usegit",
                      default=False)
    options, args = parser.parse_args()
    if options.show_version:
        print '3.X.X-X'
        sys.exit(0)

    if options.verbose:
        print "Running Insights Core Egg"
        sys.exit(0)

    sys.exit(0)

if __name__ == '__main__':
    main()