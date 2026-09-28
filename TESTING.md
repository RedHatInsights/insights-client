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

## Universal `check_*` fixtures — FAIL vs ERROR in JUnit

Integration tests use autouse fixtures whose names start with `check_`
(e.g. `check_avcs`, `check_no_egg_content`). These run during pytest
teardown after every test.

By default pytest reports any teardown exception as **ERROR**, which
Jenkins, Polarion, and UMB gating interpret as "the harness broke" rather
than "the test failed." This masks real product issues and can block
gating pipelines.

The `pytest-client-tools` `pytest_runtest_makereport` hook reclassifies
teardown failures from `check_*` fixtures as
**FAIL** so they appear correctly in JUnit XML and downstream reporting.
The hook matches on traceback frame name (any frame starting with
`check_`), not on exception type, so any exception raised inside a
`check_*` fixture is reclassified.

Fixtures that do **not** start with `check_` are left as ERROR, since
those represent genuine infrastructure problems.

## SELinux AVC collection

`pytest-client-tools` provides the single autouse `check_avcs` fixture used by
integration tests. When auditd is running and the required audit tools are
available, it checks the test's audit window with `aureport --avc --interpret`,
writes the report to that test's `artifacts/.../selinux.log`, and fails the test
with any denial that is not on the project-supplied skip list. It accepts both
the legacy and RHEL 10 `aureport` header layouts.

Known AVC exceptions and their Jira references live in each consumer project.
Insights-client keeps its rules in `integration-tests/insights_selinux.py` and
provides the rules applicable to each test through the `client_tools_avc_skips`
fixture in `integration-tests/conftest.py`. The auditctl AVC tracked by
[RHEL-246545](https://redhat.atlassian.net/browse/RHEL-246545) is listed in both
Insights-client and RHC because it applies to both projects and is seen on RHEL 10.
pytest-client-tools applies the rules supplied by the project. AVC query failures
fail the test with an `AVC check could not run` message. The insights-client fixture
`wait_for_services_during_avc_capture` keeps relevant background services
inside the same test window. SELinux tier2 tests can request `check_avcs` to
inspect the collected window while the fixture still performs the final
unexpected-denial check.
