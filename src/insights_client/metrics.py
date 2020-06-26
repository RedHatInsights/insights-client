import socket

import requests


class MetricsHTTPClient(requests.Session):
    """
    MetricsHTTPClient is a `requests.Session` subclass, configured to transmit
    runtime metrics about insights-client back to the Insights Platform.
    """

    def __init__(self, cert_file, key_file, base_url=None):
        """
        __init__ creates and configures a new MetricsHTTPClient

        :param cert: path to certificate
        :param key: path to private key
        """
        super(MetricsHTTPClient, self).__init__()
        self.cert = (cert_file, key_file)
        if base_url is None:
            for base_url in [
                "cert.cloud.redhat.com",
                "cert-api.access.redhat.com",
            ]:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((base_url, 443))
                    self.base_url = base_url
                    break
                except Exception as e:
                    print(e)
                finally:
                    s.close()
        else:
            self.base_url = base_url
        if self.base_url is None:
            raise Exception("Unable to connect to Red Hat Insights Platform")

    def post(self, event):
        """
        post sends `event` to the Insights Platform.

        :param event: a dictionary describing an event object
        """
        if self.base_url == "cert-api.access.redhat.com":
            api_prefix = "/r/insights/platform"
        else:
            api_prefix = "/api"
        url = "https://{}{}/module-update-router/v1/event".format(
            self.base_url, api_prefix
        )
        return super(MetricsHTTPClient, self).post(url, json=event)
