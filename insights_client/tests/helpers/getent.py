# -*- coding: utf-8 -*-

from os.path import join

PASSWD_PATH = join('etc', 'passwd')
GROUP_PATH = join('etc', 'group')


def passwd_exists(username, file):
    """
    Checks whether a user with a given name exists in the given passwd database.
    """
    def matcher(line):
        """
        Matches a line corresponding to a user with a given name.
        """
        return ColonSeparatedLine(line)[0] == username

    database = Database(file)
    return database.exists(matcher)


def group_exists(groupname, file):
    """
    Checks whether a group with a given name exists in the given group database.
    """
    def matcher(line):
        """
        Matches a line corresponding to a group with a given name.
        """
        return ColonSeparatedLine(line)[0] == groupname

    database = Database(file)
    return database.exists(matcher)


class ColonSeparatedLine:
    """
    Database consisting of lines with colon-separated values.
    """

    def __init__(self, line):
        """
        Splits the raw colon-separated text line into items.
        """
        self.data = line.split(':')

    def __getitem__(self, item):
        """
        Gets a specific item from the parsed line.
        """
        return self.data[item]


class Database:
    """
    Generic system entity database. Allows to find a record.
    """
    def __init__(self, file):
        """
        Stores the absolute database file path.
        """
        self.file = file

    def find(self, matcher):
        """
        Finds and returns the matching line. Arguments are passed to the self.matcher method.
        """
        try:
            while True:
                line = self.file.readline()
                if not line:  # EOF
                    return None

                if matcher(line):
                    return line.rstrip()
        finally:
            self.file.seek(0)

    def exists(self, *args, **kwargs):
        """
        Tries to find the line returning True/False depending on whether it exists or not.
        """
        return self.find(*args, **kwargs) is not None
