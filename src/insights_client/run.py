import os
import sys

from insights import package_info

import metrics
import utc

try:
    try:
        from insights.client.phase import v1 as client
    except ImportError as e:
        sys.exit(
            "Error importing insights.client for %s as %s: %s"
            % (os.environ["INSIGHTS_PHASE"], os.environ["PYTHONPATH"], e)
        )

    phase = getattr(client, os.environ["INSIGHTS_PHASE"])
    metrics_client = metrics.MetricsHTTPClient()
    code = 0
    try:
        with open("/etc/insights-client/machine-id") as f:
            machine_id = f.read()
    except:
        machine_id = "00000000-0000-0000-0000-000000000000"

    event = {
        "phase": os.environ["INSIGHTS_PHASE"],
        "started_at": utc.make_utc_datetime_rfc3339(),
        "exit": code,
        "exception": None,
        "ended_at": None,
        "machine_id": machine_id,
        "core_version": package_info["VERSION"],
        "core_path": os.environ["PYTHONPATH"],
    }
    try:
        sys.exit(phase())
    except Exception as e:
        event["exception"] = "{0}".format(e)
        code = 1
    except SystemExit as e:
        code = e.code
    finally:
        event["exit"] = code
        event["ended_at"] = utc.make_utc_datetime_rfc3339()
        metrics_client.post(event)
        sys.exit(code)
except KeyboardInterrupt:
    sys.exit(1)
except Exception as e:
    print("Error: {0}".format(e))
    sys.exit(1)
