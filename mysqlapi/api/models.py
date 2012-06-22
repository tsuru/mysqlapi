from django.db import connection

import uuid
import hashlib


def generate_password():
    return hashlib.sha1(uuid.uuid4().hex).hexdigest()

class DatabaseManager(object):

    def __init__(self, name):
        self.name = name
        self.host = "localhost"
        self.port = "3306"
        self._password = None
        self.cursor = connection.cursor()

    @property
    def password(self):
        if not self._password:
            self._password = generate_password()
        return self._password

    def create(self):
        self.cursor.execute("CREATE DATABASE %s default character set utf8 default collate utf8_general_ci" % self.name)

    def drop(self):
        self.cursor.execute("DROP DATABASE %s" % self.name)

    def create_user(self):
        self.cursor.execute("grant all privileges on %s.* to %s@%s identified by '%s'" % (self.name, self.name, self.host, self.password))

    def drop_user(self):
        self.cursor.execute("drop user %s@%s" % (self.name, self.host))
