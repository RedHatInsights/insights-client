"""
Core
"""
import sys

class InsightsCore(object):
    

    def __init__(self, mode='json', options=None):
        self.mode = mode
        self.options = options

    def run(self):
        run_mode = 'run_'+self.mode
        print 'running in mode %s' % (self.mode)
        try:
            run_func = getattr(self, run_mode)
            run_func()
        except Exception:
            sys.exit('Core mode %s not found.' % (self.mode))

    def run_archive(self):
        print "Running core in Archive mode"
        return None

    def run_json(self):
        json_facts = {'fact1': 'result1', 'fact2': 'result2'}
        if self.options is not None:
            if self.options.verbose is True:
                print json_facts
        return json_facts