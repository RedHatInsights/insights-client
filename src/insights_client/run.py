import os
import sys

from insights import package_info

import metrics

try:
    try:
        from insights.client.phase import v1 as client
    except ImportError as e:
        sys.exit(
            "Error importing insights.client for %s as %s: %s"
            % (os.environ["INSIGHTS_PHASE"], os.environ["PYTHONPATH"], e)
        )

    phase = getattr(client, os.environ["INSIGHTS_PHASE"])
    metrics_client = metrics.MetricsHTTPClient(
        cert_file="/etc/pki/consumer/cert.pem",
        key_file="/etc/pki/consumer/key.pem",
        config_file="/etc/insights-client/insights-client.conf",
    )
    code = 0
    try:
        with open("/etc/insights-client/machine-id") as f:
            machine_id = f.read()
    except:
        machine_id = "00000000-0000-0000-0000-000000000000"

    class UTC(datetime.tzinfo):
        """
        UTC is a concrete subclass of datetime.tzinfo representing the UTC
        time zone.
        """

        def utcoffset(self, dt):
            return datetime.timedelta(0)

        def tzname(self, dt):
            return "UTC"

        def dst(self, dt):
            return datetime.timedelta(0)

    def make_utc_datetime_rfc3339():
        return (
            datetime.datetime.utcnow()
            .replace(microsecond=0, tzinfo=UTC())
            .isoformat("T")
        )

    event = {
        "phase": os.environ["INSIGHTS_PHASE"],
        "started_at": make_utc_datetime_rfc3339(),
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
        event["exception"] = e
        code = 1
    except SystemExit as e:
        code = e.code
    finally:
        event["exit"] = code
        event["ended_at"] = make_utc_datetime_rfc3339()
        metrics_client.post(event)
        sys.exit(code)
except KeyboardInterrupt:
    sys.exit(1)
except Exception as e:
    print("Error: {}".format(e))
    sys.exit(1)
