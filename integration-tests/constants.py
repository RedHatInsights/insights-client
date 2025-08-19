import pathlib

HOST_DETAILS: str = "/var/lib/insights/host-details.json"
REGISTERED_FILE: str = "/etc/insights-client/.registered"
UNREGISTERED_FILE: str = "/etc/insights-client/.unregistered"
MACHINE_ID_FILE: str = "/etc/insights-client/machine-id"
TAGS_FILE = pathlib.Path("/etc/insights-client/tags.yaml")
CONFIG_FILE = "/etc/insights-client/insights-client.conf"
