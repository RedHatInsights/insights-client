#!/bin/bash

set -xe

cd "${MESON_SOURCE_ROOT}"

declare -a PROGRAMS
PROGRAMS+=(
    curl
)

for PROGRAM in "${PROGRAMS[@]}"; do
    if ! which "${PROGRAM}"; then
        echo "missing required program: ${PROGRAM}"
        exit 1
    fi
done

TAG=$(cat EGG_VERSION)

curl https://gitlab.cee.redhat.com/insights-release-eng/insights-core-assets/-/raw/$TAG/insights-core.egg --output data/rpm.egg
curl https://gitlab.cee.redhat.com/insights-release-eng/insights-core-assets/-/raw/$TAG/insights-core.egg.asc --output data/rpm.egg.asc
curl https://gitlab.cee.redhat.com/insights-release-eng/insights-core-assets/-/raw/$TAG/uploader.v2.json --output data/.fallback.json
curl https://gitlab.cee.redhat.com/insights-release-eng/insights-core-assets/-/raw/$TAG/uploader.v2.json.asc --output data/.fallback.json.asc