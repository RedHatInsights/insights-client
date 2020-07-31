import re

import requests
import rhsm
from six.moves import configparser

AUTH_METHOD_BASIC = "BASIC"
AUTH_METHOD_CERT = "CERT"


class MetricsHTTPClient(requests.Session):
    """
    MetricsHTTPClient is a `requests.Session` subclass, configured to transmit
    runtime metrics about insights-client back to the Insights Platform.
    """

    def __init__(
        self, cert_file=None, key_file=None, base_url=None, config_file=None,
    ):
        """
        __init__ creates and configures a new MetricsHTTPClient

        :param cert: path to certificate
        :param key: path to private key
        """
        super(MetricsHTTPClient, self).__init__()

        cfg = configparser.RawConfigParser()
        cfg.read(config_file)

        rhsm_cfg = rhsm.config.initConfig()
        rhsm_server_hostname = rhsm_cfg.get("server", "hostname")
        rhsm_server_port = rhsm_cfg.get("server", "port")

        match = re.match("subscription.rhsm(.stage)?.redhat.com", rhsm_server_hostname)
        if match is None:
            # Assume Satellite-managed and configure for Satellite-proxied access
            self.base_url = rhsm_server_hostname
            self.port = rhsm_server_port
            self.cert = (cert_file, key_file)
            self.api_prefix = "/redhat_access/r/insights/platform"
        else:
            try:
                auth_method = cfg.get("insights-client", "authmethod")
            except configparser.NoOptionError:
                auth_method = AUTH_METHOD_CERT

            if auth_method == AUTH_METHOD_BASIC:
                self.base_url = "cloud.redhat.com"
                self.port = 443
                u = cfg.get("insights-client", "username")
                p = cfg.get("insights-client", "password")
                self.auth = (u, p)
                self.api_prefix = "/api"

            if auth_method == AUTH_METHOD_CERT:
                self.base_url = "cert.cloud.redhat.com"
                self.port = 443
                self.cert = (cert_file, key_file)
                self.api_prefix = "/api"

    def post(self, event):
        """
        post sends `event` to the Insights Platform.

        :param event: a dictionary describing an event object
        """
        url = "https://{}:{}{}/module-update-router/v1/event".format(
            self.base_url, self.port, self.api_prefix
        )
        return super(MetricsHTTPClient, self).post(url, json=event)
