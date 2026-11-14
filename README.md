# Red Hat Insights Client

**insights-client** is a wrapper for Insights Core (the egg).

## Developer Setup

Follow these instructions to prepare your system for development.

1. Fork both this and the [insights-core](https://github.com/RedHatInsights/insights-core) repository.

2. Clone both of them to the same directory:

   ```shell
   $ git clone git@github.com:$YOU/insights-client.git
   $ git clone git@github.com:$YOU/insights-core.git
   ```

3. Make sure your virtual environment uses system site packages.

   - For existing one, set `include-system-site-packages = true` in virtual environment's `pyvenv.cfg`.
   - For new one, create it with `--system-site-packages` flag.
   - Make sure both repositories share the virtual environment.

4. Install the `insights-core` as a Python package.

   First, make sure the following directories and files exist, otherwise the code will scream at you:
 
   ```shell
   $ sudo mkdir -p /etc/insights-client
   $ sudo ln -s `pwd`/data/etc/cert-api.access.redhat.com.pem /etc/insights-client/
   ```

   Then you can install the package using pip:

   ```shell
   $ cd insights-client
   $ python3 -m pip install --upgrade pip wheel
   $ python3 -m pip install -e ../insights-core/.[client-develop]
   ```

5. Run the client.

   ```shell
   $ sudo PYTHONPATH=./src:../insights-core python3 src/insights_client/__init__.py --help
   ```


### Contributing

- Every relevant change should have a test, if possible.
- Every commit containing Python code should be formatted with `black`.
- Every commit/PR will be checked for those in CI.
- Read [TESTING.md](TESTING.md) for more information.


## Integration test configuration

Integration tests (via [pytest-client-tools](https://github.com/RedHatInsights/pytest-client-tools)) read their configuration with dynaconf from `settings.toml` at the repository root. The file is **not committed**: when `SETTINGS_URL` is set (most likely in `.testing-farm.yaml`), `systemtest/tests/integration/test.sh` downloads a **sanitized, non-secret `settings.toml`** served by auto-services, backing up any pre-existing local file as `settings.toml.bak`. Locally you can instead provide your own git-ignored `settings.toml` and/or `.secrets.toml`.

The served file contains only non-secret values (hosts, ports, URLs, client IDs, orgs). **Secrets are neither committed nor served** — provide them as environment variables (or a local `.secrets.toml`). The secret keys consumed by this repository's integration tests are:

| Environment variable | Settings key | Used by |
|----------------------|--------------|---------|
| `PYTEST_CLIENT_TOOLS_CANDLEPIN__PASSWORD` | `candlepin.password` | `register_subman` fixture (non-Satellite registration) |
| `PYTEST_CLIENT_TOOLS_CANDLEPIN__ACTIVATION_KEYS` | `candlepin.activation_keys` | `register_subman` fixture (Satellite registration) |
| `PYTEST_CLIENT_TOOLS_AUTH_PROXY__USERNAME` | `auth_proxy.username` | `test_register_auth_proxy`, `test_auth_proxy_connection` |
| `PYTEST_CLIENT_TOOLS_AUTH_PROXY__PASSWORD` | `auth_proxy.password` | `test_register_auth_proxy`, `test_auth_proxy_connection` |

Note: Satellite environments (`ENV_FOR_DYNACONF=satellite617`, `satellite618`, `satellite619`, `satellite-capsule`) also require `PYTEST_CLIENT_TOOLS_CANDLEPIN__PASSWORD`. The value is never used for registration there — activation keys do the work — but the served `settings.toml` has `username = ""` in every Satellite section and pytest-client-tools validates that `candlepin.password` exists whenever `candlepin.username` exists; without it the config fails to load and every satellite test errors. Any non-empty dummy value satisfies the validator, though the real account password is recommended.

Notes:

- Nested keys use `PYTEST_CLIENT_TOOLS_<SECTION>__<KEY>` (each `.` becomes `__`, uppercased); flat keys use `PYTEST_CLIENT_TOOLS_<KEY>`. Values are parsed as TOML, so lists must be quoted: `'["key1", "key2"]'`.
- Precedence is environment variables > `.secrets.toml` > `settings.toml` > defaults; no file needs to exist.
- `ENV_FOR_DYNACONF` selects the environment (section) to use: `default` (default), `stage`, `prod`, `satellite617`, `satellite618`, `satellite619`, `satellite-capsule`, `testing`.

### Sanitization of the served settings (CCT-3160)

Previously, the file served from `SETTINGS_URL` included secrets and was downloaded over plain HTTP before the test run. The served file is now sanitized — secrets are stripped from it and must be provided via the environment variables above (or a git-ignored local `.secrets.toml`). If you still keep a local plaintext `settings.toml` with secrets, **delete it**.

`settings.toml` remains a downloaded artifact: it is git-ignored and never committed. When `SETTINGS_URL` is set, `systemtest/tests/integration/test.sh` backs up any existing `settings.toml` and downloads the sanitized file; for purely local runs, unset `SETTINGS_URL` and provide your own `settings.toml`/`.secrets.toml` instead.


## Legacy Architecture Summary

insights-client product consists of two parts: insights-client (wrapper) and insights-core. Historically, the Core (also named the Egg) has been distributed through CDN, with an older, frozen version packaged within insights-client itself. Later, the Core delivery model was changed to be RPM as well.

Wrapper is the entry point providing CLI on $PATH, and ensures [**phases**](#phases) are run.

Egg is a bundle that contains the `insights` package with all the main functionality. All flags and configurations are passed to the egg by the wrapper.

### Phases

insights-client runs in four phases.

1. **pre-update**: Execute flags that exit immediately (`--version`, `--test-connection`, `--checkin`).
2. **update**: Download new Core from CDN. This phase is not used anymore.
3. **post-update**: Process flags (like registration options), and exit if the operation requires registration and the system is not registered.
4. **collect & upload**: Run data collection, compress the results and upload them to ConsoleDot.

## Configuration

The configuration uses the values in the following hierarchy:

1. CLI flags
2. `/etc/insights-client/insights-client.conf`
3. environment variables (in a form of `INSIGHTS_xxxxxx`, where `xxxxxx` is the configuration variable name, in all caps)

### Directories
The client utilizes several directories on the system for its operation:

- `/etc/insights-client/` - The primary directory for configuration. It contains `insights-client.conf`, redaction files (`file-redaction.yaml`, `file-content-redaction.yaml`), and security certificates.
- `/var/log/insights-client/` - The default directory for log files.
- `/var/lib/insights/` - Stores information about the core module (egg), including `last_stable.egg`.
- `/var/cache/insights-client/` - The default location where the archive is stored when the `--keep-archive`, `--no-upload` and `--offline` flags are used.
- `/var/tmp/` - Used as a temporary location for building the archive before upload.

## Log Management
The client logs its activity to provide a record of its operations, which is essential for troubleshooting. 
All of the following switches were already explained in the **Configuration** section.

### Log File
By default, all log output is sent to `/var/log/insights-client/insights-client.log`.

### Log Verbosity
The level of detail in the logs can be controlled.

1. The `--verbose` flag increases the verbosity to `DEBUG` level for a single run. (More logs)
2. The `--quiet` flag decreases verbosity to only show `ERROR` messages.

## External Services
When you run `insights-client`, it connects to several Red Hat services. Connectivity to these services is required for a standard, non-offline execution.

### Red Hat Insights API
These are the primary services the client communicates with.

Purpose: To upload the collected system data archive, download updated insights-core, and retrieve analysis results. It can also optionally connect to services for Compliance and Malware detection.

Hostnames: The default hostname is `cert-api.access.redhat.com`. For newer infrastructure, `cert.cloud.redhat.com` is also used.

### Automatic Configuration via RHSM
If the system is registered to RHSM, the insights-client may reconfigure itself to use Satellite hostname.

If registered to a Red Hat Satellite server:
The client will automatically reconfigure itself. It uses the Satellite's hostname as the destination for data uploads.

If not registered to a Satellite server:
The client operates in its default mode. It connects directly to the primary Red Hat Insights API, which is the standard behavior for systems registered with Red Hat.

This entire auto-detection process is based on reading **local** config files only (managed by RHSM).

examples of what you could see in logs if `auto_config=True`:  
`DEBUG insights.client.auto_config:159 Connected to staging RHSM, using cert.cloud.stage.redhat.com`  
`DEBUG insights.client.auto_config:81 Not connected to Satellite, skipping branch_info`
