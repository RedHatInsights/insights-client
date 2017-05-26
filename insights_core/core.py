"""
Core
"""

class InsightsCore(object):
    

    def __init__(self, mode='json'):
        self.mode = mode

    def run(self):
        run_mode = 'run_'+self.mode
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
        print json_facts
        return json_facts