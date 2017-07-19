# !/usr/bin/python

from setuptools import setup, find_packages
import subprocess

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

if __name__ == "__main__":

    subprocess.call("cat {0} | gzip > {0}.gz".format(MAN_PAGE), shell=True)
    subprocess.call("cat {0} | gzip > {0}.gz".format(CONF_PAGE), shell=True)

    # where stuff lands
    logpath = "/var/log/insights-client"
    confpath = "/etc/insights-client"
    man5path = "/usr/share/man/man5/"
    man8path = "/usr/share/man/man8/"

    setup(
        name="insights-client",
        author="Richard Brantley <rbrantle@redhat.com>, Jeremy Crafts <jcrafts@redhat.com>, Dan Varga <dvarga@redhat.com>",
        author_email="rbrantle@redhat.com, jcrafts@redhat.com",
        license="GPL",
        version=VERSION,
        packages=find_packages(),
        install_requires=['requests'],
        include_package_data=True,
        scripts=[
            "scripts/insights-client"
        ],
        entry_points={'console_scripts': [
            'insights-client = insights_client:_main',
            'insights-client-run = insights_client.run:_main'
        ]},
        data_files=[
            # config files
            (confpath, ['etc/insights-client.conf',
                        'etc/.fallback.json',
                        'etc/.fallback.json.asc',
                        'etc/redhattools.pub.gpg',
                        'etc/api.access.redhat.com.pem',
                        'etc/cert-api.access.redhat.com.pem',
                        'etc/.exp.sed',
                        'etc/insights-client.cron']),

            # man pages
            (man5path, ['docs/insights-client.conf.5']),
            (man8path, ['docs/insights-client.8']),

            (logpath, [])
        ],
        description=SHORT_DESC,
        long_description=LONG_DESC
    )
