#!/usr/bin/python2


def version():
    with open("/etc/redhat-release") as fp:
        r = fp.read().strip()

    return r.split("release")[1].strip().split()[0]


def major_version():
    v = version()
    return v.split(".")[0]


def minor_version():
    v = version()
    return v.split(".")[1]


if __name__ == "__main__":
    print(major_version())
