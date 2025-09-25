# Red Hat Insights Client

**insights-client** is a wrapper for Insights Core (the egg).

## Developer Setup

Follow these instructions to prepare your system for development.

1. Fork both this and [insights-core](https://github.com/RedHatInsights/insights-core) repository.

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
   $ sudo ln -s `pwd`/data/redhattools.pub.gpg /etc/insights-client/
   $ sudo ln -s `pwd`/data/cert-api.access.redhat.com.pem /etc/insights-client/
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
- `/var/cache/insights-client/` - The default location where the archive is stored when the `--keep-archive`, `--no-upload` and `--offline` flag is used.
- `/var/tmp/` - Used as a temporary location for building the archive before upload.

## Log Management
The developer logs its activity to provide a record of its operations, which is essential for troubleshooting. 
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
This are the primary services the client communicates with.

Purpose: To upload the collected system data archive, download updated insights-core, and retrieve analysis results. It can also optionally connect to services for Compliance and Malware detection.

Hostnames: The default hostname is `cert-api.access.redhat.com`. For newer infrastructure, `cert.cloud.redhat.com` is also used.

### Automatic Configuration via RHSM
If the system is registered to RHSM, the insights-client may reconfigure itself to use Satellite hostname.

If registered to a Red Hat Satellite server:
The client will automatically reconfigure itself. It uses the Satellite's hostname as the destination for data uploads.

If not registered to a Satellite server:
The client operates in its default mode. It connects directly to the primary Red Hat Insights API, which is the standard behavior for systems registered with Red Hat.

This entire auto-detection process is based on reading **local** config files only (managed by RHSM).

examples what you could see in logs if `auto_config=True`:  
`DEBUG insights.client.auto_config:159 Connected to staging RHSM, using cert.cloud.stage.redhat.com`  
`DEBUG insights.client.auto_config:81 Not connected to Satellite, skipping branch_info`
