# !/usr/bin/python

from setuptools import setup, find_packages
import subprocess
from insights_client.major_version import major_version

rhel_version = int(major_version())


def get_version():
    f = open('insights_client/constants.py')
    for line in f:
        if 'version' in line:
            return eval(line.split('=')[-1])


VERSION = get_version().split('-')[0]
MAN_PAGE = "docs/insights-client.8"
CONF_PAGE = "docs/insights-client.conf.5"
SHORT_DESC = "Red Hat Insights"
LONG_DESC = """
Uploads insightful information to Red Hat
"""

requires = ['requests', 'PyYaml', 'six', 'pyOpenSSL']

if __name__ == "__main__":

    subprocess.call("cat {0} | gzip > {0}.gz".format(MAN_PAGE), shell=True)
    subprocess.call("cat {0} | gzip > {0}.gz".format(CONF_PAGE), shell=True)

    # where stuff lands
    logpath = "/var/log/insights-client"
    confpath = "/etc/insights-client"
    systemdpath = "/usr/lib/systemd/system"
    man5path = "/usr/share/man/man5/"
    man8path = "/usr/share/man/man8/"
    conf_files = ['etc/insights-client.conf',
                  'etc/.fallback.json',
                  'etc/.fallback.json.asc',
                  'etc/redhattools.pub.gpg',
                  'etc/cert-api.access.redhat.com.pem',
                  'etc/.exp.sed',
                  'etc/rpm.egg',
                  'etc/rpm.egg.asc']

    if rhel_version == 6:
        conf_files.append('etc/insights-client.cron')

    data_files = [
        # config files
        (confpath, conf_files),

        # man pages
        (man5path, ['docs/insights-client.conf.5']),
        (man8path, ['docs/insights-client.8']),

        (logpath, []),
    ]

    if rhel_version >= 7:
        data_files.append(
            (systemdpath, ['etc/insights-client.service', 'etc/insights-client.timer'])
        )

    setup(
        name="insights-client",
        author="Richard Brantley <rbrantle@redhat.com>, Jeremy Crafts <jcrafts@redhat.com>, Dan Varga <dvarga@redhat.com>",
        author_email="rbrantle@redhat.com, jcrafts@redhat.com",
        license="GPL",
        version=VERSION,
        packages=find_packages(),
        install_requires=requires,
        extras_require={'develop': requires + ['flake8']},
        include_package_data=True,
        entry_points={'console_scripts': [
            'redhat-access-insights = insights_client:_main',
            'insights-client = insights_client:_main',
            'insights-client-run = insights_client.run:_main'
        ]},
        data_files=data_files,
        description=SHORT_DESC,
        long_description=LONG_DESC
    )
