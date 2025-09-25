import os
import sys

import logging

logger = logging.getLogger(__name__)

try:
    try:
        from insights.client.phase import v2 as client
    except ImportError as e:
        sys.exit(
            "Error importing insights.client for %s as %s: %s"
            % (os.environ["INSIGHTS_PHASE"], os.environ["PYTHONPATH"], e)
        )

    phase = getattr(client, os.environ["INSIGHTS_PHASE"])
    sys.exit(phase())
except KeyboardInterrupt:
    sys.exit(1)
except Exception as e:
    print("Fatal: {0}".format(e))
    sys.exit(1)
