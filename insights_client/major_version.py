#!/usr/bin/python2


def major_version():
    return 7
    with open("/etc/redhat-release") as fp:
        r = fp.read().strip()

    release = r.split("release")[1].strip()
    return release.split()[0].split(".")[0]


if __name__ == "__main__":
    print(major_version())
