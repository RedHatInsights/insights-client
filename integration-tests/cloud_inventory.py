"""Helpers for cloud Inventory auth checks in integration tests."""

import logging
import os
import types

import pytest
import requests

logger = logging.getLogger(__name__)

CONSUMER_CERT = "/etc/pki/consumer/cert.pem"
CONSUMER_KEY = "/etc/pki/consumer/key.pem"
_AUTH_FAILURES = frozenset({401, 500, 502, 503, 504})

_state = types.SimpleNamespace(auth_ok=None, reason=None)


class CloudInventoryAuthError(Exception):
    """Raised when cloud Inventory returns 401/5xx during an auth probe."""


def skip_if_auth_unavailable():
    """Skip the current test if a prior probe found Inventory auth unavailable."""
    if _state.auth_ok is False:
        logger.info(
            "Skipping test: cloud inventory auth previously unavailable (%s)",
            _state.reason,
        )
        pytest.skip(_state.reason)


def probe_cloud_inventory_auth(insights_client):
    """Probe Inventory auth.

    Raises CloudInventoryAuthError on HTTP 401/5xx.
    Transport errors are logged and ignored (not treated as auth failures).
    """
    host = insights_client.get_services_api_host()
    insights_id = getattr(insights_client, "uuid", None) or ("00000000-0000-0000-0000-000000000000")
    url = f"https://{host}/api/inventory/v1/host_exists?insights_id={insights_id}"
    try:
        response = requests.get(url, cert=(CONSUMER_CERT, CONSUMER_KEY), timeout=30)
    except requests.exceptions.RequestException as exc:
        logger.warning("cloud inventory probe transport error: %s", exc)
        # Transport errors are not the 401/5xx auth noise this gate targets.
        return

    if response.status_code in _AUTH_FAILURES:
        raise CloudInventoryAuthError(
            f"cloud inventory auth unavailable: HTTP {response.status_code}"
        )


def ensure_cloud_inventory(insights_client):
    """Skip or xfail when cloud Inventory auth returns 401/5xx.

    Call immediately before ``wait_for_inventory`` / ``wait_for_advisor``.

    - First definitive 401/5xx in the session → ``pytest.skip`` (later marked
      tests are skipped by the autouse fixture in conftest).
    - 401/5xx after a successful probe earlier in the session → ``pytest.xfail``,
      and later marked tests skip without re-probing.
    """
    skip_if_auth_unavailable()

    if not (os.path.exists(CONSUMER_CERT) and os.path.exists(CONSUMER_KEY)):
        return

    try:
        probe_cloud_inventory_auth(insights_client)
        _state.auth_ok = True
    except CloudInventoryAuthError as exc:
        reason = str(exc)
        previously_ok = _state.auth_ok is True
        _state.auth_ok = False
        _state.reason = reason
        if previously_ok:
            logger.info(
                "Xfailing test: cloud inventory auth failed after earlier success (%s)",
                reason,
            )
            pytest.xfail(reason)

        logger.info("Skipping test: %s", reason)
        pytest.skip(reason)
