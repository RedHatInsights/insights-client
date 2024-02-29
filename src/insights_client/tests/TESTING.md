# Testing `insights-client`

After installing the prerequisites, you can run the unit test suite using `pytest`:

```shell
$ python -m pip install -r src/insights_client/tests/requirements.txt
$ python -m pytest src/insights_client/tests
```

## Specifying the egg

You need to point the `EGG` environment variable to a valid path of the egg.

## CI

The unit tests are also run by GitHub Actions.
