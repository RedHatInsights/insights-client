"""
Ansible
"""
import sys
import os
from constants import InsightsConstants as constants
from utilities import InsightsUtilities

class InsightsAnsible(object):
    

    def __init__(self, core, inventory=None, egg_path=None):
        self.ansible = None
        self.ansible_loaded = False
        self.core = core
        self.inventory = inventory
        self.egg_path = egg_path
        self.utilities = InsightsUtilities()
        self.load_ansible()

    def load_ansible(self):
        try:
            import ansible
            self.ansible = ansible
            self.ansible_loaded = True
            return True
        except Exception:
            return False

    def get_egg_path(self):
        return '/usr/lib/python2.7/site-packages/insights-core.egg'

    def run(self):
        try:
            inventory = self.inventory if self.inventory is not None else constants.default_ansible_inventory
            egg_path = self.egg_path if self.egg_path is not None else self.get_egg_path()
            ansible_command = 'ansible %s -m insights -a "egg_path=%s"' % (inventory, egg_path)
            print "Running command %s" % (ansible_command)
            env = os.environ.copy()
            env['ANSIBLE_LIBRARY'] = "/etc/insights-client"
            ansible_execution = self.utilities.run_command_get_output(ansible_command, env)
            print "Ansible execution Status:"
            print ansible_execution['status']
            print "Ansible execution Output:"
            print ansible_execution['output']
        except Exception as an_exception:
            print an_exception
            sys.exit("Could not run the Ansible action plugin and module. Exiting.")
