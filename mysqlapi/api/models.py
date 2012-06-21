from django.db import connection

import uuid
import hashlib


class DatabaseManager(object):

    def __init__(self, name):
        self.name = name
        self.host = "localhost"
        self.port = "3306"

    @property
    def password(self):
        return hashlib.sha1(uuid.uuid4().hex).hexdigest()

    def create(self):
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE %s default character set utf8 default collate utf8_general_ci" % self.name)

    def drop(self):
        cursor = connection.cursor()
        cursor.execute("DROP DATABASE %s" % self.name)

    def create_user(self):
        cursor = connection.cursor()
        cursor.execute("grant all privileges on %s.* to %s@%s identified by '%s'" % (self.name, self.name, self.host, self.password))

    def drop_user(self):
        cursor = connection.cursor()
        cursor.execute("drop user %s@%s" % (self.name, self.host))
