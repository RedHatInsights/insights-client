#!/usr/bin/python3

# Request testing
# TESTING_FARM_API_TOKEN=... testing-farm request --no-wait --context test_event=ctc --environment SETTINGS_URL=http://auto-services.usersys.redhat.com/automation-properties/settings.toml --compose RHEL-10-Nightly

# Download tf resutls.xml (with links to files): https://artifacts.osci.redhat.com/testing-farm/${request_id}/results.xml

# Download /testsuites/testsuite/testcase/logs[name="data/junit.xml"]

# Run betelgeuse
#         cp $WORKSPACE/junit*.xml $WORKSPACE/${projectName}/
#         cd $WORKSPACE/${projectName}
#         echo "Converting results to Polarion format..."
#         PYTHONPATH=integration-tests/ betelgeuse --config-module custom_betelgeuse_config \
#         test-run \
#         --custom-fields '{"composeid":"${testImage}","arch":"${archCustom}","description":"${description}","poolteam":"${poolteam}","component":"${component}","fips":"${fips}","assignee":"${assignee}"}' \
#         --test-run-title "${testRunTitle}" \
#         --no-include-skipped \
#         $WORKSPACE/${projectName}/junit*.xml \
#         ./integration-tests/ \
#         automation \
#         RHELSS \
#         test_run.xml
#
# Upload to Polarion
#         echo "Uploading to Polarion..."
#         curl -k -u "$POLARION_USER:$POLARION_PASS" \
#         -X POST \
#         -F file=@test_run.xml \
#         https://polarion.engineering.redhat.com/polarion/import/xunit
#
#         echo "Polarion upload complete"
