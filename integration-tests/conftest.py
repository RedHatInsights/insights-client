import pytest


@pytest.fixture(scope="session")
def register_subman(external_candlepin, subman_session, test_config):
    subman_session.register(
        username=test_config.get("candlepin", "username"),
        password=test_config.get("candlepin", "password"),
    )
    yield subman_session
