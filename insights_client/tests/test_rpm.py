# -*- coding: utf-8 -*-

import pytest

from .helpers.getent import group_exists, GROUP_PATH, passwd_exists, PASSWD_PATH
from os import getenv, listdir, makedirs, remove
from os.path import abspath, exists, join
from pipes import quote
from re import escape, match
from subprocess import check_call


# Run the tests in this file only if they are explicitly enabled by setting environment variable TEST_RPM=True.
# The reason for that is that installing a package with all its dependencies requires network connection, a lot of disk
# writes and space, running commands with sudo and it takes a long time.
test_rpm = getenv('TEST_RPM')
if test_rpm == "True":
    skip_tests = False
elif test_rpm == "False" or test_rpm is None:
    skip_tests = True
else:
    raise ValueError("TEST_RPM={} is not a valid value. Provide True/False.".format(test_rpm))
skip_mark = pytest.mark.skipif(skip_tests, reason="RPM tests are resource-heavy and require root privileges.")

CURRENT_PATH = abspath('.')
DIST_PATH = join(CURRENT_PATH, "tmp", "dist")
RPM_PATH = join(DIST_PATH, "RPMS", "noarch")
JAIL_PATH = join(CURRENT_PATH, "tmp", "jail")

JAIL_GROUP_PATH = join(JAIL_PATH, GROUP_PATH)
JAIL_PASSWD_PATH = join(JAIL_PATH, PASSWD_PATH)

PACKAGE_NAME = "insights-client"
TARBALL_PATTERN = "^{}-.+\\.tar\\.gz$".format(escape(PACKAGE_NAME))
RPM_PATTERN = "^{}-.+\\.noarch\\.rpm$".format(escape(PACKAGE_NAME))

GROUPNAME = 'insights'
USERNAME = GROUPNAME


class FileNotFoundError(LookupError):
    """
    No file with a matching name has been found.
    """
    pass


def sudo_check_call(original_command, *args, **kwargs):
    """
    Runs a command using check_call with sudo.
    """
    sudo_command = ("sudo",) + original_command
    return check_call(sudo_command, *args, **kwargs)


def find_file_by_pattern(path, pattern):
    """
    Finds the exact path of a first file in the given directory that matches the given pattern.
    """
    entries = listdir(path)
    for entry in entries:
        if match(pattern, entry):
            return join(path, entry)

    raise FileNotFoundError("File matching /{}/ not found.".format(pattern))


def yum_command(command, *args):
    """
    Composes a yum command that runs automatically in the jail environment.
    """
    return ("yum", command, "--assumeyes", "--installroot={}".format(JAIL_PATH), "--releasever=/") + args


def sudo_check_call_yum_remove():
    """
    Remove the package.
    """
    remove_command = yum_command('remove', PACKAGE_NAME)
    sudo_check_call(remove_command)


def sudo_check_call_yum_install():
    """
    Install the built RPM with all its dependencies.
    """
    rpm_path = find_file_by_pattern(RPM_PATH, RPM_PATTERN)
    install_command = yum_command('install', rpm_path)
    sudo_check_call(install_command)


def setup_function():
    """
    Prepares a “chroot”-like environment into which the package can be installed.
    """

    if exists(DIST_PATH):
        try:
            tarball_path = find_file_by_pattern(DIST_PATH, TARBALL_PATTERN)
        except FileNotFoundError:
            return None
        else:
            remove(tarball_path)

    # Can’t use `make rpm`, since it does not respect the RPMTOP path in all steps.
    # @TODO: Fix the Makefile.
    py_sdist = "PY_SDIST=python setup.py sdist --dist-dir={}".format(quote(DIST_PATH))
    check_call(("make", "tarball", py_sdist))

    # This is the part that does not work well in the Makefile.
    define_topdir = "--define=_topdir {}".format(DIST_PATH)
    define_sourcedir = "--define=_sourcedir {}".format(DIST_PATH)
    tarball_path = find_file_by_pattern(DIST_PATH, TARBALL_PATTERN)
    check_call(("rpmbuild", "-ts", define_topdir, define_sourcedir, tarball_path))

    # When the srpm is built the right way, it’s possible to leave building the binary rpm to the Makefile.
    rpmtop = "RPMTOP={}".format(DIST_PATH)
    check_call(("make", "rpm", rpmtop))

    if exists(JAIL_PATH):
        # The “chroot” already exists, the package can be installed there. Remove it so it can be installed again.
        sudo_check_call_yum_remove()
    else:
        # Prepare the “chroot”.
        makedirs(JAIL_PATH)


@skip_mark
def test_remove_passwd():
    sudo_check_call_yum_install()

    with open(JAIL_PASSWD_PATH) as file:
        assert passwd_exists(USERNAME, file)

    sudo_check_call_yum_remove()

    with open(JAIL_PASSWD_PATH) as file:
        assert not passwd_exists(USERNAME, file)


@skip_mark
def test_remove_group():
    sudo_check_call_yum_install()

    with open(JAIL_GROUP_PATH) as file:
        assert group_exists(GROUPNAME, file)

    sudo_check_call_yum_remove()

    with open(JAIL_GROUP_PATH) as file:
        assert not group_exists(GROUPNAME, file)
