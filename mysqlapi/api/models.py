from django.db import connection
from django.conf import settings

from mysqlapi.api.database import Connection

import hashlib
import subprocess
import uuid


def generate_password():
    return hashlib.sha1(uuid.uuid4().hex).hexdigest()


def generate_user(username):
    if len(username) > 16:
        _username = username[:12] + generate_password()[:4]
    else:
        _username = username
    return _username


class DatabaseManager(object):

    def __init__(self, name):
    # def __init__(self, name, host="localhost"):
        self.name = name
        # self.host = host
        self.port = '3306'
        config = settings.DATABASES["default"]
        self.conn = Connection(config.get("HOST", "localhost"), config.get("USER", ""), config.get("PASSWORD", ""), config.get("NAME", ""))
        self.cursor = connection.cursor()

    def create_database(self):
        self.conn.open()
        cursor = self.conn.cursor()
        cursor.execute("CREATE DATABASE %s default character set utf8 default collate utf8_general_ci" % self.name)
        self.conn.close()

    def drop_database(self):
        self.conn.open()
        cursor = self.conn.cursor()
        cursor.execute("DROP DATABASE %s" % self.name)
        self.conn.close()

    def create_user(self, username, host):
        self.conn.open()
        cursor = self.conn.cursor()
        username = generate_user(username)
        password = generate_password()
        cursor.execute("grant all privileges on %s.* to %s@%s identified by '%s'" % (self.name, username, host, password))
        self.conn.close()
        return username, password

    def drop_user(self, username, host):
        self.conn.open()
        cursor = self.conn.cursor()
        cursor.execute("drop user %s@%s" % (username, host))
        self.conn.close()

    def export(self):
        return subprocess.check_output(["mysqldump", "-u", "root", "-d", self.name, "--compact"], stderr=subprocess.STDOUT)
