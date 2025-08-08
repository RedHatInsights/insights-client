import pathlib

HOST_DETAILS: str = "/var/lib/insights/host-details.json"
REGISTERED_FILE: str = "/etc/insights-client/.registered"
UNREGISTERED_FILE: str = "/etc/insights-client/.unregistered"
MACHINE_ID_FILE: str = "/etc/insights-client/machine-id"
TAGS_FILE = pathlib.Path("/etc/insights-client/tags.yaml")
INSIGHTS_CLIENT_LOG_FILE = "/var/log/insights-client/insights-client.log"
CONFIG_FILE = "/etc/insights-client/insights-client.conf"
