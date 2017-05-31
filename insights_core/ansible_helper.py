"""
Ansible
"""
import sys
from constants import InsightsConstants as constants

class InsightsAnsible(object):
    

    def __init__(self, core, inventory=None):
        self.ansible = None
        self.ansible_loaded = False
        self.core = core
        self.inventory = inventory
        self.load_ansible()

    def load_ansible(self):
        try:
            import ansible
            self.ansible = ansible
            self.ansible_loaded = True
            return True
        except Exception:
            return False

    def run(self):
        try:
            pass
        except Exception as an_exception:
            print an_exception
            sys.exit("Could not run the Ansible action plugin and module. Exiting.")
