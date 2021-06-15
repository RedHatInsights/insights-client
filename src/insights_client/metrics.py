import os.path
import re

import requests
from six.moves import configparser

AUTH_METHOD_BASIC = "BASIC"
AUTH_METHOD_CERT = "CERT"


def _proxy_settings(rhsm_config):
    conf = {"hostname": None,
            "port": None,
            "user": None,
            "password": None}

    for key in conf:
        try:
            conf[key] = rhsm_config.get("server", "proxy_" + key).strip() or None
        except configparser.NoSectionError:
            return None
        except configparser.NoOptionError:
            pass
        if key == "hostname" and not conf[key]:
            # hostname is the only required value. return None if empty
            return None

    auth = "%s:%s@" % (conf["user"], conf["password"]) if conf["user"] and conf["password"] else ""
    proxy = "http://%s%s:%s" % (auth, conf["hostname"], conf["port"] or "")

    return {"https": proxy}


class MetricsHTTPClient(requests.Session):
    """
    MetricsHTTPClient is a `requests.Session` subclass, configured to transmit
    runtime metrics about insights-client back to the Insights Platform.
    """

    def __init__(
        self,
        cert_file=None,
        key_file=None,
        base_url=None,
        config_file="/etc/insights-client/insights-client.conf",
        rhsm_config_file="/etc/rhsm/rhsm.conf",
    ):
        """
        __init__ creates and configures a new MetricsHTTPClient

        :param cert: path to certificate
        :param key: path to private key
        """
        super(MetricsHTTPClient, self).__init__()

        cfg = configparser.RawConfigParser()
        cfg.read(config_file)

        rhsm_cfg = configparser.ConfigParser()
        rhsm_cfg.read(rhsm_config_file)

        try:
            rhsm_server_hostname = rhsm_cfg.get("server", "hostname").strip()
            rhsm_server_port = rhsm_cfg.get("server", "port").strip()
            rhsm_rhsm_repo_ca_cert = rhsm_cfg.get("rhsm", "repo_ca_cert").strip()
            rhsm_rhsm_consumerCertDir = rhsm_cfg.get("rhsm", "consumerCertDir").strip()
        except (configparser.NoSectionError, configparser.NoOptionError):
            # cannot read RHSM conf, go straight to insights-client conf parsing
            # set is_satellite=False to enter the insights-client.conf parsing block
            is_satellite = False
        else:
            if cert_file is None:
                cert_file = os.path.join(rhsm_rhsm_consumerCertDir, "cert.pem")
            if key_file is None:
                key_file = os.path.join(rhsm_rhsm_consumerCertDir, "key.pem")

            match = re.match("subscription.rhsm(.stage)?.redhat.com", rhsm_server_hostname)
            if match is None:
                # Assume Satellite-managed and configure for Satellite-proxied access
                self.base_url = rhsm_server_hostname
                self.port = rhsm_server_port
                self.cert = (cert_file, key_file)
                self.verify = rhsm_rhsm_repo_ca_cert
                self.api_prefix = "/redhat_access/r/insights/platform"
                is_satellite = True
            else:
                is_satellite = False

        if not is_satellite:
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

        # @TODO: Do it more like Core insight.client.connection: RHSM if auto_config, fallback to conf and then to ENV.
        #   Use NO_PROXY, custom Core proxy auth etc.
        try:
            auto_config = cfg.getboolean("insights-client", "auto_config")
        except configparser.NoOptionError:
            auto_config = True

        if auto_config:
            self.proxies = _proxy_settings(rhsm_cfg)
        else:
            self.proxies = None

    def post(self, event):
        """
        post sends `event` to the Insights Platform.

        :param event: a dictionary describing an event object
        """
        url = "https://{0}:{1}{2}/module-update-router/v1/event".format(
            self.base_url, self.port, self.api_prefix
        )
        return super(MetricsHTTPClient, self).post(url, json=event, proxies=self.proxies)
