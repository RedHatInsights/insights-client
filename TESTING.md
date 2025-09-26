# Testing `insights-client`

After installing the prerequisites, you can run the unit test suite using `pytest`:

```shell
$ python3 -m pip install -r src/insights_client/tests/requirements.txt
$ python3 -m pytest src/insights_client/tests
```

## Specifying insights-core

By default, the installed insights-core package is used to run the insights-client test suite.
By adding a custom path to a local repository of insights-core in the `PYTHONPATH` environment variable, you can test with custom insights-core versions (such as upstream HEAD, for example).


## CI

The unit tests are also run by GitHub Actions.
