#!/usr/bin/python
import os
import sys

try:
	import insights.client
except ImportError:
	sys.exit("Error importing insights.client for %s as %s" % (os.environ["INSIGHTS_PHASE"], os.environ["PYTHONPATH"]))

if os.geteuid() is not 0:
    sys.exit("Red Hat Insights must be run as root")
else:
    phase = getattr(insights.client, os.environ["INSIGHTS_PHASE"])
    sys.exit(phase())
