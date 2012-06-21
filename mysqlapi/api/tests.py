from django.test import TestCase
from django.db import connection
from django.test.client import RequestFactory

from mysqlapi.api.models import DatabaseManager
from mysqlapi.api.views import create, drop


class DatabaseViewTestCase(TestCase):

    def setUp(self):
        self.cursor = connection.cursor()

    def test_create(self):
        request = RequestFactory().post("/", {"appname": "ciclops"})
        response = create(request)
        self.assertEqual(201, response.status_code)

        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'ciclops'")
        row = self.cursor.fetchone()
        self.assertEqual("ciclops", row[0])

        self.cursor.execute("select User, Host FROM mysql.user WHERE User='ciclops' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertEqual("ciclops", row[0])
        self.assertEqual("localhost", row[1])

        db = DatabaseManager()
        db.drop_user(username="ciclops", host="localhost")
        db.drop(name="ciclops")

    def test_drop(self):
        db = DatabaseManager()
        db.create(name="ciclops")
        db.create_user(username="ciclops", host="localhost")

        request = RequestFactory().delete("/ciclops")
        response = drop(request, "ciclops")
        self.assertEqual(200, response.status_code)

        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'ciclops'")
        row = self.cursor.fetchone()
        self.assertFalse(row)

        self.cursor.execute("select User, Host FROM mysql.user WHERE User='ciclops' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertFalse(row)


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
