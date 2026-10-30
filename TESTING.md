# Testing `insights-client`

After installing the prerequisites, you can run the unit test suite using `pytest`:

```shell
$ python3 -m pip install -r src/insights_client/tests/requirements.txt
$ python3 -m pytest src/insights_client/tests
```

## Specifying the egg

By default, we are using the `rpm.egg` to run insights-client test suite.
By pointing the `EGG` environment variable to a different path, you can test custom eggs (the upstream HEAD, for example).


## CI

The unit tests are also run by GitHub Actions.

## Cloud Inventory dependent tests

Some integration tests call cloud Inventory/Advisor APIs via
`wait_for_inventory()` / `wait_for_advisor()` (from pytest-client-tools). Those
helpers retry until timeout when stage returns 401/5xx, which makes Satellite
and insights-core-assets runs hang or ERROR on service/auth noise rather than
client regressions.

Those tests are marked `requires_cloud_inventory` and call
`ensure_cloud_inventory()` from `integration-tests/cloud_inventory.py`
immediately before waiting on Inventory/Advisor:

| Test | File |
|------|------|
| `test_ultralight_checkin` | `integration-tests/test_checkin.py` |
| `test_insights_details_file_exists` | `integration-tests/test_client.py` |
| `test_set_ansible_host_info` | `integration-tests/test_client_options.py` |
| `test_check_show_results` | `integration-tests/test_client_options.py` |

### Skip vs xfail semantics

`ensure_cloud_inventory()` probes Inventory with the consumer cert against the
same services API host the wait helpers use:

- **Skip** — first HTTP 401/500/502/503/504 in the session skips that test and
  every later `requires_cloud_inventory` test, with a clear reason (for example
  `cloud inventory auth unavailable: HTTP 401`). Unmarked tests still run.
- **Xfail** — if a probe earlier in the session succeeded and a later probe
  returns 401/5xx (for example stage flapping mid-run), that individual test is
  reported as xfailed instead of hanging in `loop_until` until timeout which
  should help with stage Inventory auth failures.

## Deployment markers

`bootc_unsafe` and `satellite_unsafe` are registered in `pytest.ini`. A new tier1 test runs on both periodics until it is marked. The image-mode periodic runs `-m "tier1 and not bootc_unsafe"`. The satellite periodic runs `-m "tier1 and not satellite_unsafe"`.

Mark a tier1 test when it does not belong on that periodic:

- `bootc_unsafe` — the test installs, removes packages, or drives `bootc upgrade`, `bootc rollback`, or `bootc switch`.
- `satellite_unsafe` — the test calls cloud Inventory or Advisor (`external_inventory`, `ensure_cloud_inventory`, `wait_for_inventory`, `wait_for_advisor`).

Proxy registration, proxy connection, and `test_official_playbook` are marked with both. Compliance tests skip when `oscap` is absent.
