# -*- coding: utf-8 -*-
import json
import os

from django.test import TestCase
from django.test.client import RequestFactory

from mysqlapi.api.database import Connection
from mysqlapi.api.models import DatabaseManager
from mysqlapi.api.views import create_database


class CreateDatabaseViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = Connection(hostname="localhost", username="root")
        cls.conn.open()
        cls.cursor = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_create_database_should_returns_500_when_name_is_missing(self):
        request = RequestFactory().post("/", {})
        response = create_database(request)
        self.assertEqual(500, response.status_code)
        self.assertEqual("App name is missing", response.content)

    def test_create_database_should_returns_500_when_name_is_blank(self):
        request = RequestFactory().post("/", {"name": ""})
        response = create_database(request)
        self.assertEqual(500, response.status_code)
        self.assertEqual("App name is empty", response.content)

    def test_create_database_should_returns_500_and_error_msg_in_body(self):
        db = DatabaseManager("ciclops")
        db.create_database()
        request = RequestFactory().post("/", {"name": "ciclops"})
        response = create_database(request)
        self.assertEqual(500, response.status_code)
        self.assertEqual("Can't create database 'ciclops'; database exists", response.content)
        db.drop_database()

    def test_create_database_should_returns_405_when_method_is_not_post(self):
        request = RequestFactory().get("/")
        response = create_database(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().put("/")
        response = create_database(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().delete("/")
        response = create_database(request)
        self.assertEqual(405, response.status_code)

    def test_create_database(self):
        request = RequestFactory().post("/", {"name": "ciclops"})
        response = create_database(request)
        self.assertEqual(201, response.status_code)
        content = json.loads(response.content)
        expected = {
            u"MYSQL_DATABASE_NAME": u"ciclops",
            u"MYSQL_HOST": u"localhost",
            u"MYSQL_PORT": u"3306",
        }
        self.assertDictEqual(expected, content)

        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'ciclops'")
        row = self.cursor.fetchone()
        self.assertEqual("ciclops", row[0])

        db = DatabaseManager("ciclops")
        db.drop_database()

    def test_create_database_returns_the_host_from_environment_variable(self):
        os.environ["MYSQLAPI_DATABASE_HOST"] = "10.0.1.100"
        request = RequestFactory().post("/", {"name": "plains_of_dawn"})
        response = create_database(request)
        self.assertEqual(201, response.status_code)
        content = json.loads(response.content)
        expected = {
            u"MYSQL_DATABASE_NAME": u"plains_of_dawn",
            u"MYSQL_HOST": u"10.0.1.100",
            u"MYSQL_PORT": u"3306",
        }
        self.assertEqual(expected, content)
        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'plains_of_dawn'")
        row = self.cursor.fetchone()
        self.assertEqual("plains_of_dawn", row[0])
        db = DatabaseManager("plains_of_dawn")
        db.drop_database()

    def test_create_database_in_a_custom_service_host(self):
        request = RequestFactory().post("/", {"name": "ciclops", "service_host": "127.0.0.1"})
        response = create_database(request)
        self.assertEqual(201, response.status_code)
        content = json.loads(response.content)
        expected = {
            u"MYSQL_DATABASE_NAME": u"ciclops",
            u"MYSQL_HOST": u"127.0.0.1",
            u"MYSQL_PORT": u"3306",
        }
        self.assertDictEqual(expected, content)

        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'ciclops'")
        row = self.cursor.fetchone()
        self.assertEqual("ciclops", row[0])

        db = DatabaseManager("ciclops")
        db.drop_database()
