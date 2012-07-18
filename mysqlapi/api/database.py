import MySQLdb


class Connection(object):

    def __init__(self, hostname="localhost", username="", password="", database=""):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.database = database
        self._connection = None

    def open(self):
        if not self._connection:
            self._connection = MySQLdb.connect(self.hostname, self.username, self.password, self.database)

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

    def cursor(self):
        return self._connection.cursor()
