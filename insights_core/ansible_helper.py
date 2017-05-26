"""
Ansible
"""
import sys

class InsightsAnsible(object):
    

    def __init__(self, core):
        self.ansible = None
        self.ansible_loaded = False
        self.core = core
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
        self.core.run()
