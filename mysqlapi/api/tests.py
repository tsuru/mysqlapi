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
