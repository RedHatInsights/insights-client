#!/usr/bin/python
import os
import sys
import insights.client

if os.geteuid() is not 0:
    sys.exit("Red Hat Insights must be run as root")
else:
    phase = getattr(insights.client, os.environ["INSIGHTS_PHASE"])
    sys.exit(phase())
