# -*- coding: utf-8 -*-

import pytest
import six

from subprocess import PIPE, Popen


def run_sed(stdin):
    """
    Obfuscates given string by SED script.
    """
    pipe = Popen(['sed', '-rf', 'etc/.exp.sed'], stdin=PIPE, stdout=PIPE, stderr=PIPE, env={"LC_ALL": "C"})
    if six.PY3:
        stdout, stderr = pipe.communicate(input=stdin.encode('utf8'))
        return stdout.decode('utf8')
    else:
        stdout, stderr = pipe.communicate(input=stdin)
        return stdout


@pytest.mark.parametrize(["stdin", "obfuscated"],
                         [["password=root", "password=********"],
                          ["password=p4ssw0rd", "password=********"],
                          ["password=I!m_strong1S7arQ4ST$2bu/QurvRCjrTGWYajIMx/", "password=********"],
                          ["password=!p@4#$$w%O^r&d*p(a)s-s_w+o=r/d", "password=********"],
                          ["password_verification=root", "password_verification=********"],
                          ["password == root", "password == ********"],
                          ["password root", "password ********"],
                          ["password --md555 4facade5cafe", "password --md555 ********"],
                          ["password--md5 4facade5cafe", "password--md5 ********"],
                          ["password--sha1", "password********"],
                          [" (abc=def&password=root&key=value )", " (abc=def&password=******** )"],
                          ["password: root", "password: ********"],
                          ["{auth: {password: \"root\"}}", "{auth: {password: \"********\"}}"],
                          ["<auth \"password\"=\"root\" />", "<auth \"password\"=\"********\" />"]])
def test_fully_obfuscate(stdin, obfuscated):
    stdout = run_sed(stdin)
    assert stdout == obfuscated


@pytest.mark.parametrize(["stdin", "obfuscated"], [["password=pass word", "password=******** word"],
                                                   ["password=pass,word", "password=********,word"],
                                                   ["password=pass.word", "password=********.word"],
                                                   ["password=pass[word]", "password=********[word]"],
                                                   ["password=pass{word}", "password=********{word}"],
                                                   ["password=pass<word>", "password=********<word>"],
                                                   ["password=pas/sw\\ord", "password=********\\ord"],
                                                   ["password=passwörd", "password=********örd"],
                                                   ["password=passw٥rd", "password=********٥rd"]])
def test_partially_obfuscate(stdin, obfuscated):
    stdout = run_sed(stdin)
    assert stdout == obfuscated


@pytest.mark.parametrize(["stdin", "obfuscated"], [["password ******** root", "password ******** ********"],
                                                   ["password********  root", "password********  ********"]])
def test_obfuscate_rest(stdin, obfuscated):
    stdout = run_sed(stdin)
    assert stdout == obfuscated


@pytest.mark.parametrize(["stdin", "obfuscated"], [["password * root", "password ******** ********"],
                                                   ["password***  root", "password********  ********"],
                                                   ["password --sha1 4facade5cafe", "password ******** ********"],
                                                   ["password--sha1 4facade5cafe", "password******** ********"]])
def test_joint_obfuscation(stdin, obfuscated):
    stdout = run_sed(stdin)
    assert stdout == obfuscated
