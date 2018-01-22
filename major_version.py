#!/usr/bin/env python

with open("/etc/redhat-release") as fp:
    r = fp.read().strip()

release = r.split("release")[1].strip()
print release.split()[0].split(".")[0]
