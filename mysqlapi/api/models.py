from django.db import connection


class DatabaseManager(object):

    def create(self, name):
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE %s default character set utf8 default collate utf8_general_ci" % name)

    def drop(self, name):
        cursor = connection.cursor()
        cursor.execute("DROP DATABASE %s" % name)

    def create_user(self, username, host):
        cursor = connection.cursor()
        cursor.execute("grant all privileges on %s.* to %s@%s identified by '%s'" % (username, username, host, "123"))

    def drop_user(self, username, host):
        cursor = connection.cursor()
        cursor.execute("drop user %s@%s" % (username, host))
