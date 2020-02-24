import glob
import os
import shutil
from distutils import log
from distutils.command.clean import clean as _clean
from distutils.command.install_data import install_data as _install_data

import requests
from setuptools import find_packages, setup
from setuptools.command.install import install as _install
from setuptools.command.sdist import sdist as _sdist

COMMON_USER_OPTIONS = [
    ("libdir=", None, "installation directory for dynamic libraries"),
    ("datadir=", None, "installation directory for data files"),
    ("localstatedir=", None, "installation directory for local state files"),
    ("mandir=", None, "installation directory for man pages"),
    ("sysconfdir=", None, "installation directory for system configuration files"),
    ("systemdunitdir=", None, "installation directory for systemd unit files"),
]


def _download_extra_dist_files(cmd, force=False, install_dir=None):
    """
    _download_extra_dist_files downloads extra files necessary for inclusion
    in source distributions that are not shipped as part of the insights-client
    repository.

    - cmd: an instance of a setuptools/distutils Command subclass, such as sdist
    - force: always download the extra files, even if they already exist
    """
    for (url, dest) in [
        (
            "https://api.access.redhat.com/r/insights/v1/static/core/uploader.json",
            "etc/.fallback.json",
        ),
        (
            "https://api.access.redhat.com/r/insights/v1/static/core/uploader.json.asc",
            "etc/.fallback.json.asc",
        ),
        (
            "https://api.access.redhat.com/r/insights/v1/static/core/insights-core.egg",
            "etc/rpm.egg",
        ),
        (
            "https://api.access.redhat.com/r/insights/v1/static/core/insights-core.egg.asc",
            "etc/rpm.egg.asc",
        ),
    ]:
        if not os.path.exists(dest) or force:
            log.info("downloading %s" % os.path.basename(dest))
            r = requests.get(url)
            with open(dest, "w+b") as f:
                log.info("writing %s" % os.path.basename(dest))
                f.write(r.content)
    cmd.distribution.data_files += [
        (install_dir, ["etc/.fallback.json"]),
        (install_dir, ["etc/.fallback.json.asc"]),
        (install_dir, ["etc/rpm.egg"]),
        (install_dir, ["etc/rpm.egg.asc"]),
    ]


class sdist(_sdist):
    def run(self):
        _download_extra_dist_files(self, force=True)
        _sdist.run(self)


class install(_install):
    user_options = _install.user_options + COMMON_USER_OPTIONS

    def initialize_options(self):
        _install.initialize_options(self)
        self.libdir = None
        self.datadir = None
        self.localstatedir = None
        self.mandir = None
        self.sysconfdir = None
        self.systemdunitdir = None

    def finalize_options(self):
        _install.finalize_options(self)
        if self.prefix is None:
            self.prefix = "/usr/local"
        if self.libdir is None:
            self.libdir = os.path.join(self.prefix, "lib")
        if self.datadir is None:
            self.datadir = os.path.join(self.prefix, "share")
        if self.localstatedir is None:
            self.localstatedir = os.path.join("/", "var")
        if self.mandir is None:
            self.mandir = os.path.join(self.datadir, "man")
        if self.sysconfdir is None:
            self.sysconfdir = os.path.join("/", "etc")
        if self.systemdunitdir is None:
            self.systemdunitdir = os.path.join(self.libdir, "systemd", "system")

    def run(self):
        _download_extra_dist_files(
            self, install_dir=os.path.join(self.sysconfdir, "insights-client")
        )
        self.run_command("install_data")
        _install.run(self)


class install_data(_install_data):
    user_options = _install_data.user_options + COMMON_USER_OPTIONS

    def initialize_options(self):
        _install_data.initialize_options(self)
        self.libdir = None
        self.datadir = None
        self.localstatedir = None
        self.mandir = None
        self.sysconfdir = None
        self.systemdunitdir = None

    def finalize_options(self):
        _install_data.finalize_options(self)
        self.set_undefined_options(
            "install",
            ("libdir", "libdir"),
            ("datadir", "datadir"),
            ("localstatedir", "localstatedir"),
            ("mandir", "mandir"),
            ("sysconfdir", "sysconfdir"),
            ("systemdunitdir", "systemdunitdir"),
        )

    def run(self):
        self.data_files.append(
            (os.path.join(self.mandir, "man5"), glob.glob("docs/*.5"))
        )
        self.data_files.append(
            (os.path.join(self.mandir, "man8"), glob.glob("docs/*.8"))
        )
        self.data_files.append(
            (
                os.path.join(self.sysconfdir, "insights-client"),
                glob.glob("etc/*") + glob.glob("etc/.*"),
            )
        )
        self.data_files.append(
            (os.path.join(self.localstatedir, "lib", "insights"), [])
        )
        self.data_files.append(
            (os.path.join(self.localstatedir, "log", "insights-client"), [])
        )

        if os.path.exists(self.systemdunitdir):
            self.data_files.append(
                (
                    self.systemdunitdir,
                    ["data/insights-client.timer", "data/insights-client.service"],
                )
            )
        else:
            self.data_files.append(
                (
                    os.path.join(self.sysconfdir, "insights-client"),
                    ["data/insights-client.cron"],
                )
            )
            self.data_files.append(
                (
                    os.path.join(self.sysconfdir, "sysconfig"),
                    ["data/sysconfig/insights-client"],
                )
            )

        if os.path.exists(os.path.join(self.sysconfdir, "motd.d")):
            self.data_files.append(
                (
                    os.path.join(self.sysconfdir, "insights-client"),
                    ["data/insights-client.motd"],
                )
            )

        _install_data.run(self)


class clean(_clean):
    def run(self):
        _clean.run(self)
        for p in ["etc/rpm.egg", "etc/rpm.egg.asc"]:
            if os.path.exists(p):
                log.info("removing %s" % p)
                os.remove(p)
        for d in ["build/", "dist/"]:
            if os.path.exists(d):
                log.info("removing %s" % d)
                shutil.rmtree(d, ignore_errors=True)


def get_version():
    f = open("insights_client/constants.py")
    for line in f:
        if "version" in line:
            return eval(line.split("=")[-1])


setup(
    name="insights-client",
    author="Richard Brantley <rbrantle@redhat.com>, Jeremy Crafts <jcrafts@redhat.com>, Dan Varga <dvarga@redhat.com>",
    author_email="rbrantle@redhat.com, jcrafts@redhat.com",
    license="GPL",
    version=get_version(),
    packages=find_packages(),
    install_requires=["requests", "PyYaml", "six"],
    extras_require={"develop": ["flake8", "pytest"]},
    setup_requires=["requests"],
    entry_points={"console_scripts": ["insights-client = insights_client:_main"]},
    data_files=[],  # Data files should be added dynamically in the install_data.run() method
    description="Red Hat Insights",
    long_description="Uploads insightful information to Red Hat",
    cmdclass={
        "install": install,
        "install_data": install_data,
        "sdist": sdist,
        "clean": clean,
    },
)
