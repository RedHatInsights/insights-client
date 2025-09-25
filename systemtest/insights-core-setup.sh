#!/usr/bin/bash -ux

currDir=$PWD
cd ~/
git clone https://github.com/RedHatInsights/insights-core.git
cd insights-core
git switch $insightsCoreBranch

# Overwrite version and release of Core, to ensure we're always newer than released versions
sed -i "s/3.0.8/9.99.999/" insights/VERSION
sed -i "s/dev/0/" insights/RELEASE
