#!/usr/bin/python2
import os
import sys

try:
    if sys.argv[0] == "insights-client-run":
        sys.exit("Error insights-client-run cannot be run on its own")
    try:
        from insights.client.phase import v1 as client
    except ImportError:
        sys.exit("Error importing insights.client for %s as %s" % (os.environ["INSIGHTS_PHASE"], os.environ["PYTHONPATH"]))

    phase = getattr(client, os.environ["INSIGHTS_PHASE"])
    sys.exit(phase())
except KeyboardInterrupt:
    sys.exit(1)
