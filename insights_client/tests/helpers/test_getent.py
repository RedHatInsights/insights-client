# -*- coding: utf-8 -*-

import pytest

from .getent import group_exists, passwd_exists
from StringIO import StringIO


@pytest.mark.parametrize("file_contents", ["""\
vboxadd:x:996:1::/var/run/vboxadd:/bin/false
apache:x:48:48:Apache:/usr/share/httpd:/sbin/nologin
insights:x:999:997:Red Hat Insights:/var/lib/insights:/sbin/nologin
""",
                                           """\
vboxadd:x:996:1::/var/run/vboxadd:/bin/false
insights:x:999:997:Red Hat Insights:/var/lib/insights:/sbin/nologin
apache:x:48:48:Apache:/usr/share/httpd:/sbin/nologin
""",
                                           """\
insights:x:999:997:Red Hat Insights:/var/lib/insights:/sbin/nologin
"""
                                           ])
def test_passwd_exists(file_contents):
    file = StringIO(file_contents)
    assert passwd_exists('insights', file)


@pytest.mark.parametrize("file_contents", ["""\
vboxadd:x:996:1::/var/run/vboxadd:/bin/false
apache:x:48:48:Apache:/usr/share/httpd:/sbin/nologin
""",
                                           ""])
def test_passwd_not_exists(file_contents):
    file = StringIO(file_contents)
    assert not passwd_exists('insights', file)


@pytest.mark.parametrize("file_contents", ["""\
dbus:x:81:
insights:x:997:
cgred:x:998:
""",
                                           """\
dbus:x:81:
cgred:x:998:
insights:x:997:
                                           """,
                                           """
insights:x:997:
"""
                                           ])
def test_group_exists(file_contents):
    file = StringIO(file_contents)
    assert group_exists('insights', file)


@pytest.mark.parametrize("file_contents", ["""\
dbus:x:81:
cgred:x:998:
""",
                                           ""])
def test_group_not_exists(file_contents):
    file = StringIO(file_contents)
    assert not group_exists('insights', file)
