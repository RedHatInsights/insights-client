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


## Integration tests

We are using [`pytest-client-tools`](https://github.com/ptoscano/pytest-client-tools) to run our integration suite.

There are various ways to run it (e.g. through `tmt`, through Packit in CI), but the easiest way to run them locally is through `scripts/integration-tests.py`.

```shell
$ # Get your system ready
$ ./scripts/integration-tests.py generate-settings > settings.toml
$ ./scripts/integration-tests.py build-image
$ podman image ls -a
REPOSITORY                       TAG     IMAGE ID      CREATED         SIZE
localhost/insights-client-test   latest  9981e9c07636  30 seconds ago  461 MB
$ # Run the tests
$ ./scripts/integration-tests.py run --settings ./settings.toml
$ ./scripts/integration-tests.py run --settings ./settings.toml --egg ../insights-core/insights.zip
$ # Inspect the situation interactively
$ ./scripts/integration-tests.py shell --settings ./settings.toml --egg ../insights-core/insights.zip
```
