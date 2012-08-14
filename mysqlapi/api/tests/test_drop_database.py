# -*- coding: utf-8 -*-
from django.conf import settings
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

    def setUp(self):
        self.old_shared_server = settings.SHARED_SERVER
        settings.SHARED_SERVER = None

    def tearDown(self):
        settings.SHARED_SERVER = self.old_shared_server
        Instance.objects.all().delete()

    def create_ciclops(self):
        Instance.objects.create(name="ciclops")

    def create_fandango_shared(self):
        Instance.objects.create(name="fandango", shared=True)
        db = DatabaseManager("fandango", settings.SHARED_SERVER)
        db.create_database()

    def test_drop_should_returns_404_and_error_msg_in_body_when_the_instance_does_not_exist(self):
        request = RequestFactory().delete("/")
        response = DropDatabase().delete(request, name="doesnotexists")
        self.assertEqual(404, response.status_code)
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
        with self.assertRaises(Instance.DoesNotExist):
            Instance.objects.get(name="ciclops")

    def test_should_unauthorize_ec2_instance_before_terminate_it(self):
        self.create_ciclops()
        fake = mocks.FakeEC2Client()
        view = DropDatabase()
        view._client = fake
        request = RequestFactory().delete("/ciclops")
        resp = view.delete(request, "ciclops")
        self.assertEqual(200, resp.status_code)
        self.assertEqual([u"unauthorize instance ciclops", u"terminate instance ciclops"], fake.actions)

    def test_drop_database_with_shared_server(self):
        settings.SHARED_SERVER = "127.0.0.1"
        self.create_fandango_shared()
        view = DropDatabase()
        request = RequestFactory().delete("/fandango")
        resp = view.delete(request, "fandango")
        self.assertEqual(200, resp.status_code)
        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'fandango'")
        row = self.cursor.fetchone()
        self.assertIsNone(row)
