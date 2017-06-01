"""
Utilities
"""
import shlex
import os
from subprocess import Popen, PIPE, STDOUT

class InsightsUtilities(object):

    def __init__(self):
        pass

    def run_command_get_output(self, cmd, env=None):
        env = env if env is not None else os.environ.copy()
        proc = Popen(shlex.split(cmd.encode("utf-8")),
                     stdout=PIPE, stderr=STDOUT, env=env)
        stdout, stderr = proc.communicate()

        return {
            'status': proc.returncode,
            'output': stdout.decode('utf-8', 'ignore')
        }
