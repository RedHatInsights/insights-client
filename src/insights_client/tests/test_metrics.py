
from six.moves import configparser
from tempfile import NamedTemporaryFile

from pytest import fixture
from mock.mock import ANY
from mock.mock import Mock
from mock.mock import patch

from insights_client.metrics import MetricsHTTPClient
from insights_client.metrics import _proxy_settings, _is_offline


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
        # keep these default values initialized
        if "hostname" not in config:
            config["hostname"] = "subscription.rhsm.redhat.com"
        if "port" not in config:
            config["port"] = "443"
        config = u"""[server]
%s
%s
%s
%s
%s
%s
[rhsm]
%s
%s
""" % tuple(
            "%s = %s" % (key, config[key]) if key in config else ""
            for key in ("hostname", "port", "proxy_hostname", "proxy_port", "proxy_user", "proxy_password", "repo_ca_cert", "consumerCertDir"))
        return _tempfile(config)

    return factory

@patch("insights_client.metrics._proxy_settings")
def test_http_client_init_missing_server_section(proxy_settings, config_file_factory):
    '''
    Verify that when the "server" section is missing, RHSM configuration is ignored
    and insights-client configuration is preferred
    '''
    config_file = config_file_factory("username=testuser\npassword=testpass\nauthmethod=BASIC")
    rhsm_config_file = _tempfile("[nonsense]\ntest=test")
    metrics_client = MetricsHTTPClient(config_file=config_file.name, rhsm_config_file=rhsm_config_file.name)
    assert metrics_client.auth == ("testuser", "testpass")
    assert not metrics_client.cert
    assert metrics_client.base_url == "cloud.redhat.com"
    assert metrics_client.api_prefix == "/api"
    assert metrics_client.verify is True

@patch("insights_client.metrics._proxy_settings")
def test_http_client_init_default_cert_auth(proxy_settings, config_file_factory):
    '''
    Verify that when insights-client configuration is used, CERT auth is selected
    if no authmethod is defined in the configuration file
    '''
    config_file = config_file_factory("username=testuser\npassword=testpass")
    rhsm_config_file = _tempfile("[nonsense]\nauth=test")
    metrics_client = MetricsHTTPClient(
        config_file=config_file.name, rhsm_config_file=rhsm_config_file.name,
        cert_file="/path/to/test/cert.pem", key_file="/path/to/test/key.pem")
    assert not metrics_client.auth
    assert metrics_client.verify is True
    assert metrics_client.cert == ("/path/to/test/cert.pem", "/path/to/test/key.pem")
    assert metrics_client.base_url == "cert.cloud.redhat.com"
    assert metrics_client.api_prefix == "/api"

@patch("insights_client.metrics._proxy_settings")
def test_http_client_init_is_not_satellite(proxy_settings, config_file_factory, rhsm_config_file_factory):
    '''
    Verify that when the configured RHSM hostname matches one of the Red Hat subscription URLs,
    it is determined to NOT be a Satellite-subscribed host
    '''
    config_file = config_file_factory("")
    rhsm_config_file = rhsm_config_file_factory(hostname="subscription.rhsm.redhat.com")
    metrics_client = MetricsHTTPClient(
        config_file=config_file.name, rhsm_config_file=rhsm_config_file.name,
        cert_file="/path/to/test/cert.pem", key_file="/path/to/test/key.pem")
    assert not metrics_client.auth
    assert metrics_client.verify is True
    assert metrics_client.cert == ("/path/to/test/cert.pem", "/path/to/test/key.pem")
    assert metrics_client.base_url == "cert.cloud.redhat.com"
    assert metrics_client.api_prefix == "/api"

@patch("insights_client.metrics._proxy_settings")
def test_http_client_init_is_satellite(proxy_settings, config_file_factory, rhsm_config_file_factory):
    '''
    Verify that when the configured RHSM hostname does NOT match one of the Red Hat subscription URLs,
    it is determined to be a Satellite-subscribed host
    '''
    config_file = config_file_factory("")
    rhsm_config_file = rhsm_config_file_factory(
        hostname="satellite.example.com", port="443",
        repo_ca_cert="/path/to/cacert/cert.pem", consumerCertDir="/path/to/sat/certs")
    metrics_client = MetricsHTTPClient(
        config_file=config_file.name, rhsm_config_file=rhsm_config_file.name)
    assert not metrics_client.auth
    assert metrics_client.cert == ("/path/to/sat/certs/cert.pem", "/path/to/sat/certs/key.pem")
    assert metrics_client.port == "443"
    assert metrics_client.base_url == "satellite.example.com"
    assert metrics_client.verify == "/path/to/cacert/cert.pem"
    assert metrics_client.api_prefix == "/redhat_access/r/insights/platform"

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
    rhsm_config = configparser.ConfigParser()
    rhsm_config.read(rhsm_config_file.name)
    proxy_settings = _proxy_settings(rhsm_config)
    assert proxy_settings is None


def test_proxy_settings_only_hostname(rhsm_config_file_factory):
    rhsm_config_file = rhsm_config_file_factory(proxy_hostname="localhost")
    rhsm_config = configparser.ConfigParser()
    rhsm_config.read(rhsm_config_file.name)
    proxy_settings = _proxy_settings(rhsm_config)
    assert proxy_settings == {"https": "http://localhost:"}


def test_proxy_settings_without_auth(rhsm_config_file_factory):
    rhsm_config_file = rhsm_config_file_factory(proxy_hostname="localhost", proxy_port=3128)
    rhsm_config = configparser.ConfigParser()
    rhsm_config.read(rhsm_config_file.name)
    proxy_settings = _proxy_settings(rhsm_config)
    assert proxy_settings == {"https": "http://localhost:3128"}


def test_proxy_settings_with_empty_auth(rhsm_config_file_factory):
    rhsm_config_file = rhsm_config_file_factory(
        proxy_hostname="localhost", proxy_port=3128, proxy_user="", proxy_password="")
    rhsm_config = configparser.ConfigParser()
    rhsm_config.read(rhsm_config_file.name)
    proxy_settings = _proxy_settings(rhsm_config)
    assert proxy_settings == {"https": "http://localhost:3128"}


def test_proxy_settings_with_whitespace_auth(rhsm_config_file_factory):
    rhsm_config_file = rhsm_config_file_factory(
        proxy_hostname="localhost", proxy_port=3128, proxy_user=" ", proxy_password=" ")
    rhsm_config = configparser.ConfigParser()
    rhsm_config.read(rhsm_config_file.name)
    proxy_settings = _proxy_settings(rhsm_config)
    assert proxy_settings == {"https": "http://localhost:3128"}


def test_proxy_settings_empty_hostname(rhsm_config_file_factory):
    rhsm_config_file = rhsm_config_file_factory(proxy_hostname="")
    rhsm_config = configparser.ConfigParser()
    rhsm_config.read(rhsm_config_file.name)
    proxy_settings = _proxy_settings(rhsm_config)
    assert proxy_settings is None


def test_proxy_settings_whitespace_hostname(rhsm_config_file_factory):
    rhsm_config_file = rhsm_config_file_factory(proxy_hostname=" ")
    rhsm_config = configparser.ConfigParser()
    rhsm_config.read(rhsm_config_file.name)
    proxy_settings = _proxy_settings(rhsm_config)
    assert proxy_settings is None


def test_proxy_settings_with_auth(rhsm_config_file_factory):
    rhsm_config_file = rhsm_config_file_factory(
        proxy_hostname="localhost", proxy_port=3128, proxy_user="user", proxy_password="password"
    )
    rhsm_config = configparser.ConfigParser()
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
    rhsm_config_file = rhsm_config_file_factory(
        hostname="satellite.example.com",
        repo_ca_cert="/path/to/cacert/cert.pem", consumerCertDir="/path/to/sat/certs")
    metrics_client = MetricsHTTPClient(config_file=config_file.name, rhsm_config_file=rhsm_config_file.name)

    event = Mock()
    metrics_client.post(event)

    post.assert_called_once_with(
        "https://satellite.example.com:443/redhat_access/r/insights/platform/module-update-router/v1/event",
        json=event,
        proxies=None,
    )


@patch("insights_client.metrics.requests.Session.post")
def test_metrics_post_event_proxy(post, config_file_factory, rhsm_config_file_factory):
    config_file = config_file_factory("")
    rhsm_config_file = rhsm_config_file_factory(
        hostname="satellite.example.com",
        repo_ca_cert="/path/to/cacert/cert.pem", consumerCertDir="/path/to/sat/certs",
        proxy_hostname="localhost", proxy_port=3128, proxy_user="user", proxy_password="password"
    )
    metrics_client = MetricsHTTPClient(config_file=config_file.name, rhsm_config_file=rhsm_config_file.name)

    event = Mock()
    metrics_client.post(event)

    post.assert_called_once_with(
        "https://satellite.example.com:443/redhat_access/r/insights/platform/module-update-router/v1/event",
        json=event,
        proxies={"https": "http://user:password@localhost:3128"},
    )

@patch("insights_client.metrics.os.getenv")
def test_is_offline(os_getenv, config_file_factory):
    '''
    Verify that _is_offline() produces correct output from the given configurations

    NOTE: this test will become obsolete once InsightsConfig is used to load config
    '''
    # offline not specified
    config_file = config_file_factory("")
    cfg = configparser.RawConfigParser()
    cfg.read(config_file.name)
    os_getenv.return_value = None
    with patch('sys.argv', ['insights-client']):
        assert not _is_offline(cfg)
    # offline specified in config
    config_file = config_file_factory("offline=True\n")
    cfg = configparser.RawConfigParser()
    cfg.read(config_file.name)
    os_getenv.return_value = None
    with patch('sys.argv', ['insights-client']):
        assert _is_offline(cfg)
    # offline specified in CLI
    config_file = config_file_factory("")
    cfg = configparser.RawConfigParser()
    cfg.read(config_file.name)
    os_getenv.return_value = None
    with patch('sys.argv', ['insights-client', '--offline']):
        assert _is_offline(cfg)
    # offline specified in env
    config_file = config_file_factory("")
    cfg = configparser.RawConfigParser()
    cfg.read(config_file.name)
    os_getenv.return_value = "True"
    with patch('sys.argv', ['insights-client']):
        assert _is_offline(cfg)

@patch("insights_client.metrics._is_offline", Mock(return_value=True))
@patch("insights_client.metrics._proxy_settings")
def test_offline_no_init(_proxy_settings, config_file_factory, rhsm_config_file_factory):
    '''
    Verify that when the metrics client is set to offline, no further initialization is done
    '''
    config_file = config_file_factory("")
    rhsm_config_file = rhsm_config_file_factory()
    m = MetricsHTTPClient(config_file=config_file.name, rhsm_config_file=rhsm_config_file.name)
    assert m.offline
    assert not hasattr(m, 'base_url')
    assert not hasattr(m, 'port')
    assert not m.cert
    assert m.verify
    assert not hasattr(m, 'api_prefix')
    assert not m.auth
    assert not m.proxies
    _proxy_settings.assert_not_called()

@patch("insights_client.metrics._is_offline", Mock(return_value=False))
@patch("insights_client.metrics._proxy_settings")
def test_offline_basic_auth_no_user(_proxy_settings, config_file_factory, rhsm_config_file_factory):
    '''
    Verify that if no username is provided for BASIC auth, metrics are not sent (default to offline)
    '''
    config_file = config_file_factory("password=testpass\nauthmethod=BASIC")
    rhsm_config_file = rhsm_config_file_factory()
    metrics_client = MetricsHTTPClient(
        config_file=config_file.name, rhsm_config_file=rhsm_config_file.name)
    assert metrics_client.offline

@patch("insights_client.metrics._is_offline", Mock(return_value=False))
@patch("insights_client.metrics._proxy_settings")
def test_offline_basic_auth_no_pass(_proxy_settings, config_file_factory, rhsm_config_file_factory):
    '''
    Verify that if no password is provided for BASIC auth, metrics are not sent (default to offline)
    '''
    config_file = config_file_factory("username=testuser\nauthmethod=BASIC")
    rhsm_config_file = rhsm_config_file_factory()
    metrics_client = MetricsHTTPClient(
        config_file=config_file.name, rhsm_config_file=rhsm_config_file.name)
    assert metrics_client.offline

@patch('insights_client.metrics.requests.Session.post')
def test_offline_no_post(session_post, config_file_factory, rhsm_config_file_factory):
    '''
    Verify that when the metrics client is set to offline, no POSTs are performed
    '''
    config_file = config_file_factory("")
    rhsm_config_file = rhsm_config_file_factory()
    m = MetricsHTTPClient(config_file=config_file.name, rhsm_config_file=rhsm_config_file.name)
    m.offline = True

    m.post("test")
    session_post.assert_not_called()
