from configparser import ConfigParser
from tempfile import NamedTemporaryFile

from pytest import fixture
from mock.mock import ANY
from mock.mock import Mock
from mock.mock import patch

from insights_client.metrics import MetricsHTTPClient
from insights_client.metrics import _proxy_settings


def _tempfile(contents_string):
    file = NamedTemporaryFile()
    contents_bytes = contents_string.encode("utf-8")
    file.write(contents_bytes)
    file.seek(0)
    return file


@fixture
def config_file_factory():
    def factory(config):
        config = (
            u"""[insights-client]
%s"""
            % config
        )
        return _tempfile(config)

    return factory


@fixture
def rhsm_config_file_factory():
    def factory(**config):
        config = u"""[server]
hostname = cert-api.access.redhat.com
port = 443
proxy_hostname = %s
proxy_port = %s
proxy_user = %s
proxy_password = %s

[rhsm]
repo_ca_cert = 
consumerCertDir =
""" % (
            config.get("proxy_hostname", ""),
            config.get("proxy_port", ""),
            config.get("proxy_user", ""),
            config.get("proxy_password", ""),
        )
        return _tempfile(config)

    return factory


@patch("insights_client.metrics._proxy_settings")
def test_http_client_init_proxies_auto_config_false(proxy_settings, config_file_factory, rhsm_config_file_factory):
    config_file = config_file_factory("auto_config = False\n")
    rhsm_config_file = rhsm_config_file_factory()
    metrics_client = MetricsHTTPClient(config_file=config_file.name, rhsm_config_file=rhsm_config_file.name)
    assert metrics_client.proxies is None
    proxy_settings.assert_not_called()


@patch("insights_client.metrics._proxy_settings")
def test_http_client_init_proxies_auto_config_default(proxy_settings, config_file_factory, rhsm_config_file_factory):
    config_file = config_file_factory("")
    rhsm_config_file = rhsm_config_file_factory()
    metrics_client = MetricsHTTPClient(config_file=config_file.name, rhsm_config_file=rhsm_config_file.name)
    assert metrics_client.proxies is proxy_settings.return_value
    proxy_settings.assert_called_once()


@patch("insights_client.metrics._proxy_settings")
def test_http_client_init_proxies_auto_config_true(proxy_settings, config_file_factory, rhsm_config_file_factory):
    config_file = config_file_factory("auto_config = True\n")
    rhsm_config_file = rhsm_config_file_factory()
    metrics_client = MetricsHTTPClient(config_file=config_file.name, rhsm_config_file=rhsm_config_file.name)
    assert metrics_client.proxies is proxy_settings.return_value
    proxy_settings.assert_called_once()


@patch("insights_client.metrics.configparser.ConfigParser", **{"return_value.get.return_value": ""})
@patch("insights_client.metrics._proxy_settings")
def test_http_client_init_proxies_rhsm_config(
    proxy_settings, config_parser, config_file_factory, rhsm_config_file_factory
):
    config_file = config_file_factory("")
    rhsm_config_file = rhsm_config_file_factory()
    MetricsHTTPClient(config_file=config_file.name, rhsm_config_file=rhsm_config_file.name)
    config_parser.assert_called_once()
    config_parser.return_value.read.assert_called_once_with(rhsm_config_file.name)
    proxy_settings.assert_called_once_with(config_parser.return_value)


def test_proxy_settings_no_hostname(rhsm_config_file_factory):
    rhsm_config_file = rhsm_config_file_factory()
    rhsm_config = ConfigParser()
    rhsm_config.read(rhsm_config_file.name)
    proxy_settings = _proxy_settings(rhsm_config)
    assert proxy_settings is None


def test_proxy_settings_only_hostname(rhsm_config_file_factory):
    rhsm_config_file = rhsm_config_file_factory(proxy_hostname="localhost")
    rhsm_config = ConfigParser()
    rhsm_config.read(rhsm_config_file.name)
    proxy_settings = _proxy_settings(rhsm_config)
    assert proxy_settings == {"https": "http://localhost:"}


def test_proxy_settings_without_auth(rhsm_config_file_factory):
    rhsm_config_file = rhsm_config_file_factory(proxy_hostname="localhost", proxy_port=3128)
    rhsm_config = ConfigParser()
    rhsm_config.read(rhsm_config_file.name)
    proxy_settings = _proxy_settings(rhsm_config)
    assert proxy_settings == {"https": "http://localhost:3128"}


def test_proxy_settings_with_auth(rhsm_config_file_factory):
    rhsm_config_file = rhsm_config_file_factory(
        proxy_hostname="localhost", proxy_port=3128, proxy_user="user", proxy_password="password"
    )
    rhsm_config = ConfigParser()
    rhsm_config.read(rhsm_config_file.name)
    proxy_settings = _proxy_settings(rhsm_config)
    assert proxy_settings == {"https": "http://user:password@localhost:3128"}


@patch("insights_client.metrics.requests.Session.post")
def test_http_metrics_client_post_proxies(post, config_file_factory, rhsm_config_file_factory):
    config_file = config_file_factory("")
    rhsm_config_file = rhsm_config_file_factory()

    metrics_client = MetricsHTTPClient(config_file=config_file.name, rhsm_config_file=rhsm_config_file.name)
    metrics_client.base_url = "localhost"

    proxies = {"https": "http://user:password@localhost:3128"}
    metrics_client.proxies = proxies

    metrics_client.post({})
    post.assert_called_once_with(ANY, json=ANY, proxies=proxies)


@patch("insights_client.metrics.requests.Session.post")
def test_metrics_post_event_no_proxy(post, config_file_factory, rhsm_config_file_factory):
    config_file = config_file_factory("")
    rhsm_config_file = rhsm_config_file_factory()
    metrics_client = MetricsHTTPClient(config_file=config_file.name, rhsm_config_file=rhsm_config_file.name)

    event = Mock()
    metrics_client.post(event)

    post.assert_called_once_with(
        "https://cert-api.access.redhat.com:443/redhat_access/r/insights/platform/module-update-router/v1/event",
        json=event,
        proxies=None,
    )


@patch("insights_client.metrics.requests.Session.post")
def test_metrics_post_event_proxy(post, config_file_factory, rhsm_config_file_factory):
    config_file = config_file_factory("")
    rhsm_config_file = rhsm_config_file_factory(
        proxy_hostname="localhost", proxy_port=3128, proxy_user="user", proxy_password="password"
    )
    metrics_client = MetricsHTTPClient(config_file=config_file.name, rhsm_config_file=rhsm_config_file.name)

    event = Mock()
    metrics_client.post(event)

    post.assert_called_once_with(
        "https://cert-api.access.redhat.com:443/redhat_access/r/insights/platform/module-update-router/v1/event",
        json=event,
        proxies={"https": "http://user:password@localhost:3128"},
    )
