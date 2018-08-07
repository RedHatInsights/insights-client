# Red Hat Insights Client

**insights-client** is the Client API Wrapper for the Client API that lives in the Insights Core.

## Purpose
To summarize the needs and capabilities of the Insights Client for developer reference.

## Main Requirements
- Register the machine with the Insights API (except for containers/images, which are NOT registered)
- Collect files and run commands based on specs fetched from the Insights API
- Output collected data as: 
  - An archive uploaded to the Insights API
  - An archive saved to disk
  - An archive dumped to STDOUT as binary data
  - A JSON representation of the collected data
- Analyze the following types of machines:
  - Basic RHEL hosts
  - RHEV hypervisors
  - Docker images
  - Docker containers

## Architecture Summary
The Insights Client consists of two pieces: the main RPM-installed executable that ships with RHEL (from here on, referred to as **wrapper**), and the updatable core module (from here on, referred to as **egg**).

### Wrapper
The wrapper is the main entry point for the Insights Client.  The wrapper's job is to initiate the **phases**, described later.  For each phase, the wrapper iterates through the available eggs, and tries each in succession to perform a successful collection & upload. If an egg fails, the client will go on to try the next available egg.  If all eggs fail, execution will halt. All possible eggs are described as follows, in the order in which they are tried:

 - `ENV_EGG` - an egg specified by the environment variable `EGG`
 - `NEW_EGG` - newest available egg, if an update has been performed
 - `STABLE_EGG` - the last egg that performed a successful collection & upload
 - `RPM_EGG` - the default egg that ships with the RPM

## Egg
The egg is the bundle that contains the Insights Core module, which has all the main functionality in it.  All the options/switches/config are passed through to the egg from the wrapper.  The egg contains phase information

# At Run Time
Summary of the client's run, from start to finish.

## Configuration
Configuration follows a precedence hierarchy of CLI -> `/etc/insights-client/insights-client.conf` file -> environment variable.

### Environment Variables
Environment configuration can be used by setting environment variables with names in the format INSIGHTS_xxxxxx, where xxxxxx is the configuration variable name, in all caps.

### `/etc/insights-client/insights-client.conf` File
Configuration variables available in the configuration file and their explanations:

- `loglevel` - set the Python logger's default level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default DEBUG
- `trace` - log each line executed.  Default False
- `auto_config` - attempt to auto-configure the network connection with Satellite or RHSM.  Default True
- `authmethod` - authentication method for the Portal (BASIC, CERT). Default is BASIC
Note: when `auto_config` is enabled, CERT will be used if RHSM or Satellite is detected
- `username` - username for basic auth. Blank by default
- `password` - password for basic auth. Blank by default
- `base_url` - base url for the Insights API (cert-api.access.redhat.com:443/r/insights). This shouldn't ever need to be changed
- `proxy` - proxy URL. Blank by default
- `auto_update` - whether to update the rule spec file (insights.json). Default True
- `obfuscate` - whether to obfuscate IP addresses in collected data. Default False
- `obfuscate_hostname` - whether to obfuscate hostnames in collected data. Default False
- `no_schedule` - whether to disable creation of Insights cronjob on register. Default False
- `display_name` - custom display name to appear in the Insights web UI. Only used on machine registration. Blank by default

### Command Line Switches
Command line switches available and their explanations.

- `--register` - Register a system with the Insights API. Required for basic collection & upload, except in the case of certain targets or if `--offline` is specified
- `--display-name` - Display name to appear in the insights web UI. Only used on machine registration. This will override the same option in the insights-client.conf file.
- `--group` - Group to add the system to in the insights web UI. Only used on machine registration.
- `--retry` - Number of times to retry the collection archive upload. Default is 1.
- `--quiet` - Run with limited console output. This will only print ERROR level messages.
- `--silent` - Run with no console output at all.
- `--conf`, `-c` - Load a custom configuration file other than the default `/etc/insights-client/insights-client.conf`
- `--to-stdout` - Dump the archive contents as binary output to stdout.
- `--offline` - Run with no network connectivity at all. Implies `--no-upload` and makes machine registration unnecessary.
- `--logging-file` - Log to a file other than the default `/var/log/insights-client/insights-client.log`
- `--force-reregister` - Force a new registration. This delete's the machine's existing machine-id and registers a new one.
- `--verbose` - Run with all log output. This will print DEBUG level messages.
- `--no-upload` - Collect the archive, but do not upload it.
- `--keep-archive` - Collect the archive, and do not delete it after output.
- `--net-debug` - Show network debug messages in the console output.
- `--analyze-container` - Collect data from the system as if it were a container. Registration is unnecessary for this option. This will upload to a different API endpoint than vanilla system collection.
- `--analyze-file` - Collect data from a tar file, treat as a mountpoint. Upload to the image endpoint.
- `--analyze-mountpoint` - Collect data from a filesystem mountpoint other than the default /
- `--analyze-image-id` - Collect data from a Docker image with the specified ID


#### Switches that exit immediately
These particular switches supersede normal client operation; they skip collection and exit after printing their necessary output.

- `--version` - Print the versions of both the wrapper and egg, then exit.
- `--unregister` - Unregister this system from the Insights API.
- `--validate` - Validate the format of the remove.conf file.
- `--enable-schedule` - Enable the Insights daily cron job.
- `--disable-schedule` - Disable the Insights daily cron job.
- `--test-connection` - Run a test to confirm connectivity from the machine to the Insights API.
- `--support` - Print a log of basic diagnostics such as version, registration status, connectivity, config, etc.
- `--status` - Print the registration status.
 

#### Hidden switches
These switches are undocumented and for developer use only.

- `--compressor` - Compression format to use for the collection archive.
- `--from-stdin` - Load rule collection configuration from stdin (instead of from uploader.json)
- `--from-file` - Load rule collection configuration from a file (instead of from uploader.json)
- `--no-gpg` - Run without verifying the signature of the egg or rule collection spec.
- `--use-docker` - Use the Docker service for image & container collection
- `--use-atomic` - Use the Atomic service for image & container collection
- `--run-these` - Run a specific set of specs
- `--debug-phases` - Print info about phase execution and egg fallback
- `--to-json` - Print the collection results to the console as JSON.

## Phases
The Insights Client runs using **phases** of execution, modularized so that they if one crashes due to a bad egg, they can be resumed at the current phase using the following egg in the priority list.


### Phase I: Pre-Update
Execute any "switches that exit immediately" that were specified (except `--status` and `--unregister`), and exit if needed

### Phase II: Update
Establish a connection to Insights and update the egg if the egg available upstream is newer than newest.egg (check etags).
Download the newest version of `uploader.json` for file collection.

### Phase III: Post-Update
Process registration options.
Check registration.  If unregistered and operating in a mode in which registration is required, exit.

### Phase IV: Collect & Output
Run the collection.
Output to the desired format; default is archive uploaded to Insights.


## Collection
Insights Client has two modes of collection: files and commands. Both are implemented in `insights-core/insights/client/insights-spec.py`.


### Files
Files are collected using sed to scrape file contents, with the following caveats:
- Files defined in the `files` section of `remove.conf` are skipped completely
- Lines containing anything in the `patterns` section of `remove.conf` will be omitted from the file content
- Keywords defined in the `keywords` section of `remove.conf` will be replaced with `keyword#` in the file content.
The file contents are copied to a path within the archive defined from the `uploader.json`, which in most cases is similar or identical to its path on the filesystem mountpoint, i.e. `/etc/cluster/cluster.conf`.




### Commands
Commands are run such that their output is collected by the client, with the following caveats:
- Commands `rm`, `kill`, `reboot`, `shutdown` are never run
- Commands defined in the `commands` section of `remove.conf` are skipped completely
- Lines containing anything in the `patterns` section of `remove.conf` will be omitted from command output
- Keywords defined in the `keywords` section of `remove.conf` will be replaced with `keyword#` in the command output
- If a command does not exist, the client will gracefully report as such, and continue.
Command outputs are copied to a path within the archive `insights_commands/<command>` where `<command>` is an escaped format of the full command syntax, including arguments, i.e., `/insights_commands/df_-alP`. **In the case of container & image collection these paths may be slightly different.**



## Archive Structure
The Insights archive, regardless of collection target type (host, image, container) has the following structure:

```
insights.tar.gz
│
├───boot
│ └───...
├───branch_info <-- Satellite metadata
├───etc
│ ├───redhat-access-insights
│ │ └───machine-id <-- unique identifier for this system
│ └───...
├───insights_commands <-- output dumps of commands run by the client
│ └───...
├───proc
│ └───...
├───sys
│ └───...
├───var
└───...
```
