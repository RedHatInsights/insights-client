"""
Options
"""
import sys
import optparse

class InsightsOptions(object):
    

    def __init__(self):
      self.options = None
      self.args = None

    def get_options(self):
        if self.options != None:
            return self.options
        else:
            self.parse_options_and_args()
            return self.options

    def get_args(self):
        if self.args != None:
            return self.args
        else:
            self.parse_options_and_args()
            return self.get_args()

    def parse_options_and_args(self):
        parser = optparse.OptionParser()
        parser.add_option('--version','-v',
                          help="Display version",
                          action="store_true",
                          dest="show_version",
                          default=False)
        parser.add_option('--verbose','-V',
                          help="Run verbosely",
                          action="store_true",
                          dest="verbose",
                          default=False)
        parser.add_option('--nogpg','-G',
                          help=optparse.SUPPRESS_HELP,
                          action="store_true",
                          dest="nogpg",
                          default=False)
        parser.add_option('--devmode','-d',
                          help=optparse.SUPPRESS_HELP,
                          action="store_true",
                          dest="devmode",
                          default=False)
        parser.add_option('--usegit','-g',
                          help=optparse.SUPPRESS_HELP,
                          action="store_true",
                          dest="usegit",
                          default=False)
        parser.add_option('--dontcleanup','-c',
                          help=optparse.SUPPRESS_HELP,
                          action="store_true",
                          dest="dontcleanup",
                          default=False)
        parser.add_option('--useinstalledcore','-u',
                          help=optparse.SUPPRESS_HELP,
                          action="store_true",
                          dest="useinstalledcore",
                          default=False)
        parser.add_option('--useansible','-a',
                          help="Use Ansible for the delivery and collection mechanism, bypass auto-detection.",
                          action="store_true",
                          dest="useansible",
                          default=None)
        parser.add_option('--dontuseansible','-A',
                          help="Do not use Ansible for the delivery and collection mechanism, bypass auto-detection.",
                          action="store_true",
                          dest="dontuseansible",
                          default=None)
        parser.add_option('--returnarchive','-z',
                          help="Return an archive format of the data collection.",
                          action="store_true",
                          dest="returnarchive",
                          default=None)
        parser.add_option('--returnjson','-j',
                          help="Return json facts from data collection.",
                          action="store_true",
                          dest="returnjson",
                          default=None)
        options, args = parser.parse_args()
        self.options = options
        self.args = args
        return options, args