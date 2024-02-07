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
