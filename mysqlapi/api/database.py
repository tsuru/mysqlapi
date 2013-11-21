# -*- coding: utf-8 -*-

# Copyright 2013 mysqlapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import MySQLdb
import subprocess


class Connection(object):

    def __init__(self,
                 hostname="localhost",
                 port="3306",
                 username="",
                 password="",
                 database=""):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.database = database
        self.port = port
        self._connection = None

    def open(self):
        if not self._connection:
            self._connection = MySQLdb.connect(self.hostname,
                                               self.username,
                                               self.password,
                                               self.database)

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

    def cursor(self):
        return self._connection.cursor()


def export():
    dump_cmd = ["mysqldump",
                "-u",
                "root",
                "--quick",
                "--all-databases",
                "--compact"]
    return subprocess.check_output(dump_cmd, stderr=subprocess.STDOUT)
