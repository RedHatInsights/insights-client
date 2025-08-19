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

You can learn more about the configuration options in [Core's config.py](https://github.com/RedHatInsights/insights-core/blob/master/insights/client/config.py).

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
