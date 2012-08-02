# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.client import RequestFactory

from mysqlapi.api.database import Connection
from mysqlapi.api.models import DatabaseManager, Instance
from mysqlapi.api.tests import mocks
from mysqlapi.api.views import DropDatabase


class DropDatabaseViewTestCase(TestCase):


    @classmethod
    def setUpClass(cls):
        cls.conn = Connection(hostname="localhost", username="root")
        cls.conn.open()
        cls.cursor = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def create_ciclops(self):
        Instance.objects.create(name="ciclops")
        db = DatabaseManager("ciclops", "127.0.0.1")
        db.create_database()

    def test_drop_should_returns_500_and_error_msg_in_body(self):
        request = RequestFactory().delete("/")
        response = DropDatabase().delete(request, name="doesnotexists")
        self.assertEqual(500, response.status_code)
        self.assertEqual("Can't drop database 'doesnotexists'; database doesn't exist", response.content)

    def test_drop_should_returns_405_when_method_is_not_delete(self):
        request = RequestFactory().get("/")
        response = DropDatabase.as_view()(request, name="foo")
        self.assertEqual(405, response.status_code)

        request = RequestFactory().put("/")
        response = DropDatabase.as_view()(request, name="foo")
        self.assertEqual(405, response.status_code)

        request = RequestFactory().post("/")
        response = DropDatabase.as_view()(request, name="foo")
        self.assertEqual(405, response.status_code)

    def test_drop(self):
        self.create_ciclops()
        request = RequestFactory().delete("/ciclops")
        self.fake = mocks.FakeEC2Client()
        view = DropDatabase()
        view._client = self.fake
        response = view.delete(request, "ciclops")
        self.assertEqual(200, response.status_code)
        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'ciclops'")
        row = self.cursor.fetchone()
        self.assertFalse(row)
        with self.assertRaises(Instance.DoesNotExist):
            Instance.objects.get(name="ciclops")

    def test_drop_from_a_custom_service_host(self):
        self.create_ciclops()
        request = RequestFactory().delete("/ciclops", {"service_host": "127.0.0.1"})
        self.fake = mocks.FakeEC2Client()
        view = DropDatabase()
        view._client = self.fake
        response = view.delete(request, "ciclops")
        self.assertEqual(200, response.status_code)

        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'ciclops'")
        row = self.cursor.fetchone()
        self.assertFalse(row)

    def test_should_remove_ec2_instance(self):
        self.create_ciclops()
        self.fake = mocks.FakeEC2Client()
        view = DropDatabase()
        view._client = self.fake

        request = RequestFactory().delete("/ciclops", {"service_host": "127.0.0.1"})
        resp = view.delete(request, "ciclops")

        self.assertEqual(200, resp.status_code)
        self.assertEqual(["terminate instance ciclops"], self.fake.actions)
