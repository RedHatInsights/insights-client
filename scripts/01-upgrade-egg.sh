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

curl --fail -L https://console.redhat.com/api/v1/static/release/insights-core.el10.egg --output data/rpm.egg
curl --fail -L https://console.redhat.com/api/v1/static/release/insights-core.el10.egg.asc --output data/rpm.egg.asc
