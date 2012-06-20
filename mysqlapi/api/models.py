from django.db import connection


class DatabaseManager(object):

    def create(self, name):
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE %s default character set utf8 default collate utf8_general_ci" % name)
