import os
import sys

import logging

logger = logging.getLogger(__name__)

try:
    try:
        from insights.client.phase import v1 as client
    except ImportError as e:
        sys.exit(
            "Error importing insights.client for %s as %s: %s"
            % (os.environ["INSIGHTS_PHASE"], os.environ["PYTHONPATH"], e)
        )

    phase = getattr(client, os.environ["INSIGHTS_PHASE"])
    try:
        with open("/etc/insights-client/machine-id") as f:
            machine_id = f.read()
    except:
        machine_id = "00000000-0000-0000-0000-000000000000"

    sys.exit(phase())
except KeyboardInterrupt:
    sys.exit(1)
except Exception as e:
    print("Fatal: {0}".format(e))
    sys.exit(1)
