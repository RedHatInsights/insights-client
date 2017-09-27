#!/usr/bin/python
import os
import sys

try:
    try:
        from insights.client.phase import v1 as client
    except ImportError:
        sys.exit("Error importing insights.client for %s as %s" % (os.environ["INSIGHTS_PHASE"], os.environ["PYTHONPATH"]))

    phase = getattr(client, os.environ["INSIGHTS_PHASE"])
    sys.exit(phase())
except KeyboardInterrupt:
    sys.exit(1)
