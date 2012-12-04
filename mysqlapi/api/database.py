# -*- coding: utf-8 -*-
import MySQLdb
import subprocess


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


def export():
    return subprocess.check_output(["mysqldump", "-u", "root", "--databases", "--compact"], stderr=subprocess.STDOUT)
