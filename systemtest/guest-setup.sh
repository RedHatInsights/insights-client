#!/usr/bin/bash
# this is a general use version of the guest setup that happens in testing farm

# check for insights-client from existing repos
if ! dnf info insights-client &>/dev/null; then
  source <(cat /etc/os-release | grep ^ID)
  
  # convert os-release to copr name
  if [ "$ID" == "centos" ]; then
    DISTRO='centos-stream'
  else
    DISTRO="$ID"
  fi

  # have to pull from dnf as os-release does not follow the same format on rhel
  RELEASEVER=$(python3 -c 'import dnf, json; db = dnf.dnf.Base(); print(db.conf.substitutions["releasever"])')

  curl https://copr.fedorainfracloud.org/coprs/g/yggdrasil/latest/repo/$DISTRO-$RELEASEVER/group_yggdrasil-latest-$DISTRO-$RELEASEVER.repo \
    -o /etc/yum.repos.d/yggdrasil.repo
fi

dnf -y install insights-client
