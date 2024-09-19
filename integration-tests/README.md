# Running Betelgeuse

### Docs:
https://betelgeuse.readthedocs.io/en/stable/
https://betelgeuse.readthedocs.io/en/stable/config.html

## Test-case command
Command generates an XML file suited to be imported by the **Test Case XML Importer**. It reads the Python test suite source code and generated XML file with all the information necessary.

The `test-case` requires:

- The path to the Python test suite source code
- The Polarion project ID
- The output XML file path (will be overwritten if exists)


There should also be a custom config file specified for pythonpath for Betelgeuse to correctly read all the custom fields in the docstrings. The file is saved in integration-tests/custom_betelgeuse_config.py

Example:

```console
$ PYTHONPATH=integration-tests/ \
    betelgeuse --config-module \
    custom_betelgeuse_config test-case \
    integration-tests/ PROJECT ./test_case.xml
```

This will create a test_case.xml file in integration-tests/

## Test-run command
Command generates an XML file suited to be imported by the **Test Run XML Importer**.

It takes:

- A valid xUnit XML file
- A Python test suite where test case IDs can be found

And generates a resulting XML file with all the information necessary.

It requires:

- The path to the xUnit XML file
- The path to the Python test suite source code
- The Polarion user ID
- The Polarion project ID
- The output XML file path (will be overwritten if exists)

It is also highly recommended to use `--response-property` as it will then be easier to monitor the importer messages

Example:

```console
$ PYTHONPATH=integration-tests/ \
    betelgeuse test-run \
    --response-property property_key=property_value \
    junit.xml \
    insights-client/integration-tests \
    testuser \
    betelgeuse-test-run.xml
```

NOTE:

`--dry-run` can be used with `test-run` command when testing the functionality.