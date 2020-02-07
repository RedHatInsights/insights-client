# !/usr/bin/env python

import glob
import os

import requests
from setuptools import find_packages, setup
from setuptools.command.install import install
from setuptools.command.sdist import sdist


class insights_client_sdist(sdist):
    def finalize_options(self):
        sdist.finalize_options(self)
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
            log.info("downloading %s" % os.path.basename(dest))
            r = requests.get(url)
            with open(dest, "w+b") as f:
                log.info("writing %s" % os.path.basename(dest))
                f.write(r.content)


class insights_client_install(install):
    user_options = install.user_options + [
        ("libdir=", None, "installation directory for dynamic libraries"),
        ("datadir=", None, "installation directory for data files"),
        ("localstatedir=", None, "installation directory for local state files"),
        ("mandir=", None, "installation directory for man pages"),
        ("sysconfdir=", None, "installation directory for system configuration files"),
        ("systemdunitdir=", None, "installation directory for systemd unit files"),
    ]

    def initialize_options(self):
        install.initialize_options(self)
        self.libdir = None
        self.datadir = None
        self.localstatedir = None
        self.mandir = None
        self.sysconfdir = None
        self.systemdunitdir = None

    def finalize_options(self):
        install.finalize_options(self)
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

        data_files = [
            (os.path.join(self.mandir, "man5"), glob.glob("docs/*.5")),
            (os.path.join(self.mandir, "man8"), glob.glob("docs/*.8")),
            (
                os.path.join(self.sysconfdir, "insights-client"),
                glob.glob("etc/*") + glob.glob("etc/.*"),
            ),
            (os.path.join(self.localstatedir, "lib", "insights"), []),
            (os.path.join(self.localstatedir, "log", "insights-client"), []),
        ]

        if os.path.exists(self.systemdunitdir):
            data_files.append(
                (
                    self.systemdunitdir,
                    ["data/insights-client.timer", "data/insights-client.service"],
                )
            )

        if os.path.exists(os.path.join(self.sysconfdir, "sysconfig")):
            data_files.append(
                (
                    os.path.join(self.sysconfdir, "sysconfig"),
                    ["data/sysconfig/insights-client"],
                )
            )

        if os.path.exists(os.path.join(self.sysconfdir, "motd.d")):
            data_files.append(
                (
                    os.path.join(self.sysconfdir, "insights-client"),
                    ["data/insights-client.motd"],
                )
            )

        self.distribution.data_files = data_files


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
    entry_points={
        "console_scripts": [
            "redhat-access-insights = insights_client:_main",
            "insights-client = insights_client:_main",
        ]
    },
    data_files=[],  # Data files should be added to the list inside the finalize_options() method of the relocatable_install class
    description="Red Hat Insights",
    long_description="Uploads insightful information to Red Hat",
    cmdclass={"install": insights_client_install, "sdist": insights_client_sdist},
)
