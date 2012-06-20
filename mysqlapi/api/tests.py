from django.test import TestCase
from django.db import connection

from mysqlapi.api.models import DatabaseManager


class DatabaseTestCase(TestCase):

    def setUp(self):
        self.cursor = connection.cursor()

    def test_create(self):
        db = DatabaseManager()
        db.create(name="newdatabase")
        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'newdatabase'")
        row = self.cursor.fetchone()
        self.assertEqual("newdatabase", row[0])
        db.drop(name="newdatabase")

    def test_drop(self):
        db = DatabaseManager()
        db.create(name="otherdatabase")
        db.drop(name="otherdatabase")
        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'otherdatabase'")
        row = self.cursor.fetchone()
        self.assertFalse(row)

    def test_create_user(self):
        db = DatabaseManager()
        db.create_user(username="wolverine", host="localhost")
        self.cursor.execute("select User, Host FROM mysql.user WHERE User='wolverine' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertEqual("wolverine", row[0])
        self.assertEqual("localhost", row[1])
        db.drop_user(username="wolverine", host="localhost")

    def test_drop_user(self):
        db = DatabaseManager()
        db.create_user(username="magneto", host="localhost")
        db.drop_user(username="magneto", host="localhost")
        self.cursor.execute("select User, Host FROM mysql.user WHERE User='wolverine' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertFalse(row)
