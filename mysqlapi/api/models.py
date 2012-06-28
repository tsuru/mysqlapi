from django.db import connection
from django.conf import settings

from mysqlapi.api.database import Connection

import hashlib
import subprocess
import uuid


def generate_password():
    return hashlib.sha1(uuid.uuid4().hex).hexdigest()


class DatabaseManager(object):

    def __init__(self, name, host="localhost"):
        self.name = name
        self.host = host
        self.port = "3306"
        self._password = None
        self._username = None
        config = settings.DATABASES["default"]
        self.conn = Connection(config.get("HOST", "localhost"), config.get("USER", ""), config.get("PASSWORD", ""), config.get("NAME", ""))
        self.cursor = connection.cursor()

    @property
    def password(self):
        if not self._password:
            self._password = generate_password()
        return self._password

    @property
    def username(self):
        if not self._username:
            if len(self.name) > 16:
                self._username = self.name[:12] + generate_password()[:4]
            else:
                self._username = self.name
        return self._username

    def create(self):
        self.conn.open()
        cursor = self.conn.cursor()
        cursor.execute("CREATE DATABASE %s default character set utf8 default collate utf8_general_ci" % self.name)
        self.conn.close()

    def drop(self):
        self.conn.open()
        cursor = self.conn.cursor()
        cursor.execute("DROP DATABASE %s" % self.name)
        self.conn.close()

    def create_user(self):
        self.conn.open()
        cursor = self.conn.cursor()
        cursor.execute("grant all privileges on %s.* to %s@%s identified by '%s'" % (self.name, self.username, self.host, self.password))
        self.conn.close()

    def drop_user(self):
        self.conn.open()
        cursor = self.conn.cursor()
        cursor.execute("drop user %s@%s" % (self.name, self.host))
        self.conn.close()

    def export(self):
        return subprocess.check_output(["mysqldump", "-u", "root", "-d", self.name, "--compact"], stderr=subprocess.STDOUT)
