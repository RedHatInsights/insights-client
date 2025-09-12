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

### Environment Variables

Environment configuration can be used by setting environment variables with names in the format INSIGHTS_xxxxxx, where xxxxxx is the configuration variable name, in all caps.

### `insights-client.conf` File
Configuration variables available in the configuration file and their explanations:

- `loglevel` - set the Python logger's default level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). Default `DEBUG`
- `auto_config` - attempt to auto-configure the network connection with Satellite or RHSM. Default `True`
- `base_url` - base url for the Insights API. Default `cert-api.access.redhat.com:443/r/insights`
- `cert_verify` - path to CA cert to verify SSL against. Default `/etc/insights-client/cert-api.access.redhat.com.pem`
- `proxy` - proxy URL. Blank by default
- `auto_update` - whether to update the rule spec file (uploader.json) and the insights-core egg. Default `True`
- `obfuscate` - whether to obfuscate IP addresses in collected data. Default `False`
- `obfuscate_hostname` - whether to obfuscate hostnames in collected data. Default `False`
- `cmd_timeout` - how many seconds to allow a command to run before issuing a termination or kill signal. Default 120
- `http_timeout` - how many seconds to allow an HTTP call to execute before timing out. Default 120
- `core_collect` - if `True`, use insights-core to run collection instead of commands/files from uploader.json. Default `False`
- `redaction_file` - location of the redaction file. Default `/etc/insights-client/file-redaction.yaml`
- `content_redaction_file` - location of the content redaction file. Default `/etc/insights-client/file-content-redaction.yaml`
- `legacy_upload` - Use legacy HTTP configuration to perform the upload. Default `True`


### Command Line Switches
Command line switches available and their explanations.

- `--register` - Register a system with the Insights API. Required for basic collection & upload, except in the case of certain targets or if `--offline` is specified
- `--display-name=DISPLAYNAME` - Display name to appear in the insights web UI. This can be used at registration time, or standalone to change the display name any time.
- `--group=GROUP` - Add a tag named `group` to the system in the insights web UI and in insights-client tags file.
- `--retry=RETRIES` - Number of times to retry the collection archive upload. Default is 1.
- `--quiet` - Run with limited console output. This will only print ERROR level messages.
- `--silent` - Run with no console output at all.
- `--offline` - Run with no network connectivity at all. Implies `--no-upload` and makes machine registration unnecessary.
- `--verbose` - Run with all log output. This will print DEBUG level messages.
- `--no-upload` - Collect the archive, but do not upload it.
- `--keep-archive` - Collect the archive, and do not delete it after upload.
- `--net-debug` - Show network debug messages in the console output.
- `--output-dir=DIR` - Write the collected data to a specified directory without compression. Does not upload.
- `--output-file=FILE` - Write the collected data to a specified archive. Does not upload.
- `--build-packagecache` - Attempt to rebuild DNF or YUM cache for current archive generation.


#### Switches that exit immediately
These particular switches supersede normal client operation; they skip collection and exit after printing their necessary output.

- `--version` - Print the versions of both the wrapper and egg, then exit.
- `--unregister` - Unregister this system.
- `--display-name=DISPLAYNAME` - When used without `--register`, change the display name and exit.
- `--validate` - Validate the format of the remove.conf file.
- `--enable-schedule` - Enable the Insights systemd job.
- `--disable-schedule` - Disable the Insights systemd job.
- `--test-connection` - Run a test to confirm connectivity from the machine to the Insights API.
- `--support` - Print a log of basic diagnostics such as version, registration status, connectivity, config, etc.
- `--status` - Print the registration status.
- `--payload=PAYLOAD` - Upload a specified file `PAYLOAD`. Requires `--content-type`
- `--content-type=CONTENTTYPE` - Specify the console.redhat.com platform-specific content type for `--payload` option.
- `--diagnosis` - Retrieve a diagnosis for this host.
- `--compliance` - Perform a compliance upload.
- `--show-results` - Log the cached system profile to console. See also: `--check-results` under **Hidden switches**

#### Hidden switches
These switches are undocumented and for developer use only.

- `--no-gpg` - Run without verifying the signature of the egg or rule collection spec.
- `--debug-phases` - Print info about phase execution and egg fallback
- `--to-json` - Print the collection results to the console as JSON. Deprecated as rule results are no longer returned by the upload service.
- `--check-results` - Fetch the system profile and cache it. Produces no output to console. Not meant to be run as a standalone option but rather as part of a regular systemd job that refreshes the cached data.

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

## Recommended Developer Config
For convenience, some sample configs are provided here for developers for connecting to the different environments the client can interface with. These configurations can be defined via config file or via environment variables using the naming described under **Environment Variables**. The following are in config file notation and can be used as drop-in configuration.

### Stage (RHSM Auth)
**Note:** This configuration assumes that the system is registered to Stage RHSM. Insights Client will autoconfigure to interface with stage.
```
[insights-client]
proxy=http://squid.corp.redhat.com:3128
```
### Prod (RHSM Auth)
```
[insights-client]
auto_config=False
legacy_upload=False
base_url=cert.cloud.redhat.com/api
cert_verify=True
```
### Prod [classic API] (RHSM Auth)
No additional configuration is required beyond the defaults. Insights Client will autoconfigure to interface with classic prod.


## Collection

Insights Client utilizes **insights-core** to perform data collection. Details on the workings of insights-core can be found here: https://github.com/RedHatInsights/insights-core#documentation.

### Archive Structure
The Insights archive has the following structure:

```
insights.tar.gz
│
├───blacklist_report    <-- Usage metrics for file redaction
├───branch_info         <-- Satellite metadata
├───collection_stats    <-- Collection execution metrics (e.g., elapsed time, command exit codes)
├───data
│   ├───boot
│   │   └───...
│   ├───etc
│   │   ├───insights-client
│   │   │   └───machine-id  <-- unique identifier for this system
│   │   └───...
│   ├───insights_commands   <-- output dumps of commands
│   │   └───...
│   ├───proc
│   │   └───...
│   ├───sys
│   │   └───...
│   └───var
│       └───...
├───display_name        <-- Display name of this host, if specified
├───egg_release         <-- Record of the egg release channel
├───metadata            <-- Metadata generated by insights-core
│   └───...
├───tags.json           <-- Tags for this host
└───version_info        <-- Record of the client and core versions
```

## Legacy Collection
**Note:** This method of collection is deprecated in favor of **core collection** and is planned to be removed in a future release.

Insights Client's classic collection has two parts: files and commands. Both are implemented in `insights-core/insights/client/insights_spec.py`.

### Files
Files are collected using sed to scrape file contents, with the following caveats:
- Files defined in the `files` section of `file-redaction.yaml` are skipped completely
- Lines containing anything in the `patterns` section of `file-content-redaction.yaml` will be omitted from the file content
- Keywords defined in the `keywords` section of `file-content-redaction.yaml` will be replaced with `keyword#` in the file content.
The file contents are copied to a path within the archive defined from the `uploader.json`, which in most cases is similar or identical to its path on the filesystem mountpoint, i.e. `/etc/cluster/cluster.conf`.

### Commands
Commands are run such that their output is collected by the client, with the following caveats:
- Commands `rm`, `kill`, `reboot`, `shutdown` are never run
- Commands defined in the `commands` section of `file-redaction.yaml` are skipped completely
- Lines containing anything in the `patterns` section of `file-content-redaction.yaml` will be omitted from command output
- Keywords defined in the `keywords` section of `file-content-redaction.yaml` will be replaced with `keyword#` in the command output
- If a command does not exist, the client will gracefully report as such, and continue.
Command outputs are copied to a path within the archive `insights_commands/<command>` where `<command>` is an escaped format of the full command syntax, including arguments, i.e., `/insights_commands/df_-alP`.

### Archive Structure (Legacy)
The **legacy** Insights archive has the following structure:

```
insights.tar.gz
│
├───blacklist_report    <-- Usage metrics for file redaction
├───boot
│   └───...
├───branch_info         <-- Satellite metadata
├───collection_stats    <-- Collection execution metrics (e.g., elapsed time, command exit codes)
├───display_name        <-- Display name of this host, if specified
├───egg_release         <-- Record of the egg release channel
├───etc
│   ├───insights-client
│   │   └───machine-id    <-- unique identifier for this system
│   └───...
├───insights_commands   <-- output dumps of commands
│   └───...
├───proc
│   └───...
├───sys
│   └───...
├───tags.json           <-- Tags for this host
├───var
│   └───...
└───version_info        <-- Record of the client and core versions
```
