# Red Hat Insights Client

**insights-client** is the Client API Wrapper for the Client API that lives in the Insights Core (the egg).

## Developer Setup

These instructions require the system to be registered with Red Hat Subscription Management.

1. Fork both this and [insights-core](https://github.com/RedHatInsights/insights-core) repository.

2. Clone both of them to the same directory:

   ```shell
   $ git clone git@github.com:$YOU/insights-client.git
   $ git clone git@github.com:$YOU/insights-core.git
   ```

3. If you are using a virtual environment for development, make sure that it uses the system site packages.

   - For existing one, set `include-system-site-packages = true` in virtual environment's `pyvenv.cfg`.
   - For new one, create it with `--system-site-packages` flag.
   - Make sure both repositories share the virtual environment.

4. Install the `insights-core` as a package.

   First, make sure the following directories and files exist, otherwise the code will scream at you:
 
   ```shell
   $ sudo mkdir -p /etc/insights-client
   $ sudo touch /etc/insights-client/.exp.sed
   ```
   
   Then you can install the package using pip:

   ```shell
   $ cd insights-client
   $ python3 -m pip install --upgrade pip wheel
   $ python3 -m pip install -e ../insights-core/.[client-develop]
   ```

5. Set up the build directory.

   ```shell
   $ meson setup builddir
   $ meson compile -C builddir
   $ chmod +x ./builddir/src/insights-client
   ```

6. Run the client with the following options to disable GPG since the development eggs are unsigned.

   ```shell
   $ sudo PYTHONPATH=./src BYPASS_GPG=True EGG=../insights-core ./builddir/src/insights-client --no-gpg --help
   ```

   *Note: `BYPASS_GPG` skips the verification on insights-client side, `--no-gpg` disables it on insights-core/egg side.*

7. To build an insights-core egg from source, run `build_client_egg.sh` from the insights-core repo.

   ```shell
   $ cd ../insights-core
   $ bash build_client_egg.sh
   $ # File `insights.zip` gets created in the current directory
   $ cd ../insights-client
   $ # To use the zip file as an egg, pass `EGG=../insights-core/insights.zip`
   ```


## Architecture Summary

The Insights Client consists of two pieces: the main RPM-installed executable that ships with RHEL (the `insights-client` repository, from here on referred to as **wrapper**), and the updatable core module (the `insights-core` repository, from here on referred to as **egg**).

### Wrapper

The wrapper is the main entry point for the Insights Client, and its job is to initiate the [**phases**](#phases). For each phase, the wrapper iterates over the available eggs, and tries each in succession to perform a collection & upload. If an egg fails, the client will try the next available egg. If all eggs fail, execution will halt. All possible eggs are described as follows, in the order in which they are tried:

 1. `ENV_EGG` - an egg specified by the environment variable `EGG`,
 2. `NEW_EGG` - newest available egg, if an update has been performed,
 3. `STABLE_EGG` - the last egg that performed a successful collection & upload,
 4. `RPM_EGG` - the default egg that ships with the RPM.

### Egg

The egg is a bundle that contains the Insights Core module with all the main functionality. All flags and configurations are passed to the egg by the wrapper.


## Phases

The Insights Client runs in four phases.
They are modularized, so if one of them crashes due to a bad egg, the proces can be resumed at that phase using the egg that's next in the priority list.

   1. **Pre-Update**  
   Execute any flags that exit immediately (except `--status` and `--unregister`).
   If necessary, exit.

   2. **Update**  
   Establish a connection to Insights and update the local egg if the upstream contains a newer version (using etags).
   During legacy collection, download the newest version of `uploader.json`.

   3. **Post-Update**  
   Process registration options.
   Check registration.
   If the system is not registered and the operation requires the registration, exit.

   4. **Collect and output**  
   [Run the collection](#collection).
   Output it in desired format; the default is to upload the archive to Insights.


## Configuration

The configuration file uses INI format (see [configparser](https://docs.python.org/3/library/configparser.html)).
The main section for configuration variables is `[insights-client]`.

The configuration uses the values in the following hierarchy:

1. CLI flags
2. `/etc/insights-client/insights-client.conf`
3. environment variables.

### Environment Variables

Environment configuration can be used by setting environment variables with names in the format INSIGHTS_xxxxxx, where xxxxxx is the configuration variable name, in all caps.

### `insights-client.conf` File
Configuration variables available in the configuration file and their explanations:

- `loglevel` - set the Python logger's default level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). Default `DEBUG`
- `auto_config` - attempt to auto-configure the network connection with Satellite or RHSM. Default `True`
- `authmethod` - authentication method for the Portal (BASIC, CERT). Default is `BASIC`
Note: when `auto_config` is enabled, `CERT` will be used if RHSM or Satellite is detected
- `username` - username for basic auth. Blank by default
- `password` - password for basic auth. Blank by default
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
- `--group=GROUP` - Group to add the system to in the insights web UI. Only used on machine registration.
- `--retry=RETRIES` - Number of times to retry the collection archive upload. Default is 1.
- `--quiet` - Run with limited console output. This will only print ERROR level messages.
- `--silent` - Run with no console output at all.
- `--conf`, `-c` - Load a custom configuration file other than the default `/etc/insights-client/insights-client.conf`
- `--offline` - Run with no network connectivity at all. Implies `--no-upload` and makes machine registration unnecessary.
- `--logging-file` - Log to a file other than the default `/var/log/insights-client/insights-client.log`
- `--force-reregister` - Force a new registration. This delete's the machine's existing machine-id and registers a new one.
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
- `--unregister` - Unregister this system from the Insights API.
- `--display-name=DISPLAYNAME` - When used without `--register`, change the display name and exit.
- `--validate` - Validate the format of the remove.conf file.
- `--enable-schedule` - Enable the Insights systemd job.
- `--disable-schedule` - Disable the Insights systemd job.
- `--test-connection` - Run a test to confirm connectivity from the machine to the Insights API.
- `--support` - Print a log of basic diagnostics such as version, registration status, connectivity, config, etc.
- `--status` - Print the registration status.
- `--payload=PAYLOAD` - Upload a specified file `PAYLOAD`. Requires `--content-type`
- `--content-type=CONTENTTYPE` - Specify the console.redhat.com platform-specific content type for `--payload` option.
- `--diagnosis=ID` - Retrieve remediations for this host, optionally providing a diagnosis ID.
- `--compliance` - Perform a compliance upload.
- `--show-results` - Log the cached system profile to console. See also: `--check-results` under **Hidden switches**

#### Hidden switches
These switches are undocumented and for developer use only.

- `--no-gpg` - Run without verifying the signature of the egg or rule collection spec.
- `--debug-phases` - Print info about phase execution and egg fallback
- `--to-json` - Print the collection results to the console as JSON. Deprecated as rule results are no longer returned by the upload service.
- `--check-results` - Fetch the system profile and cache it. Produces no output to console. Not meant to be run as a standalone option but rather as part of a regular systemd job that refreshes the cached data.


## Recommended Developer Config
For convenience, some sample configs are provided here for developers for connecting to the different environments the client can interface with. These configurations can be defined via config file or via environment variables using the naming described under **Environment Variables**. The following are in config file notation and can be used as drop-in configuration.

### CI (Basic Auth)
**Note:** CI requires basic auth.
```
[insights-client]
auto_config=False
username=<username>
password=<password>
legacy_upload=False
base_url=ci.cloud.redhat.com/api
cert_verify=False
```
### QA (Basic Auth)
**Note:** QA requires basic auth.
```
[insights-client]
auto_config=False
username=<username>
password=<password>
legacy_upload=False
base_url=qa.cloud.redhat.com/api
cert_verify=False
```
### Stage (RHSM Auth)
**Note:** This configuration assumes that the system is registered to Stage RHSM. Insights Client will autoconfigure to interface with stage.
```
[insights-client]
proxy=http://squid.corp.redhat.com:3128
```
### Stage (Basic Auth)
```
[insights-client]
auto_config=False
username=<username>
password=<password>
legacy_upload=False
base_url=cert.cloud.stage.redhat.com/api
cert_verify=True
proxy=http://squid.corp.redhat.com:3128
```
### Prod (RHSM Auth)
```
[insights-client]
auto_config=False
authmethod=CERT
legacy_upload=False
base_url=cert.cloud.redhat.com/api
cert_verify=True
```
### Prod (Basic Auth)
```
[insights-client]
auto_config=False
username=<username>
password=<password>
legacy_upload=False
base_url=cert.cloud.redhat.com/api
cert_verify=True
```
### Prod [classic API] (RHSM Auth)
No additional configuration is required beyond the defaults. Insights Client will autoconfigure to interface with classic prod.

### Prod [classic API] (Basic Auth)
```
[insights-client]
auto_config=False
username=<username>
password=<password>
```


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
