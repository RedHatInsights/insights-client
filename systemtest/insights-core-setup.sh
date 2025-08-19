#!/usr/bin/bash -x

currDir=$PWD
cd ~/
REPO="${insightsCoreRepo:-https://github.com/RedHatInsights/insights-core.git}"
git clone $REPO
cd $(basename $_ .git)
git switch "$insightsCoreBranch"

# Overwrite version and release of Core, to ensure we're always newer than released versions
sed -i "s/3.0.8/9.99.999/" insights/VERSION
sed -i "s/dev/0/" insights/RELEASE

# TODO Install it as a Python package to the system
#  Without it, this setup script is effectively broken.

cd $currDir
