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
