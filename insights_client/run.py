#!/usr/bin/python
import os
import sys
from insights.client import run

# Require Root to run
if os.geteuid() is not 0:
    sys.exit("Red Hat Insights must be run as root")

sys.exit(run())
