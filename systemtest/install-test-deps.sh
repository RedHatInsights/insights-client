#!/bin/bash
set -ux

dnf --setopt install_weak_deps=False install -y \
  bzip2 \
  bzip2-devel \
  git-core \
  insights-client \
  logrotate \
  man-db \
  openscap \
  openscap-scanner \
  podman \
  python3-pip \
  python3-pytest \
  scap-security-guide \
  zip
