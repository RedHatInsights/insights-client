#!/usr/bin/env python
import sys
import logging

__author__ = 'Richard Brantley <rbrantle@redhat.com>'
LOG_FORMAT = ("%(asctime)s %(levelname)s %(message)s")
APP_NAME = 'insights-client'
logger = logging.getLogger(APP_NAME)

def main():
	'''
	Main entry point
	'''
	print "Running Insights Client"
	sys.exit(0)

if __name__ == '__main__':
    main()