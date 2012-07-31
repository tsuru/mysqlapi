# -*- coding: utf-8 -*-
import json
import os

from boto.ec2.regioninfo import RegionInfo
from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory
from mocker import Mocker

from mysqlapi.api.database import Connection
from mysqlapi.api.models import DatabaseManager
from mysqlapi.api.tests import mocks
from mysqlapi.api.views import CreateDatabase


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
        view = CreateDatabase()
        view._ec2_conn = mocks.FakeEC2Conn()
        response = view.post(request)
        self.assertEqual(500, response.status_code)
        self.assertEqual("App name is missing", response.content)

    def test_create_database_should_returns_500_when_name_is_blank(self):
        request = RequestFactory().post("/", {"name": ""})
        view = CreateDatabase()
        view._ec2_conn = mocks.FakeEC2Conn()
        response = view.post(request)
        self.assertEqual(500, response.status_code)
        self.assertEqual("App name is empty", response.content)

    def test_create_database_should_returns_500_and_error_msg_in_body(self):
        db = DatabaseManager("ciclops")
        db.create_database()
        request = RequestFactory().post("/", {"name": "ciclops"})
        view = CreateDatabase()
        view._ec2_conn = mocks.FakeEC2Conn()
        response = view.post(request)
        self.assertEqual(500, response.status_code)
        self.assertEqual("Can't create database 'ciclops'; database exists", response.content)
        db.drop_database()

    def test_create_database_should_returns_405_when_method_is_not_post(self):
        request = RequestFactory().get("/")
        view = CreateDatabase()
        response = view.dispatch(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().put("/")
        response = view.dispatch(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().delete("/")
        response = view.dispatch(request)
        self.assertEqual(405, response.status_code)

    def test_create_database(self):
        request = RequestFactory().post("/", {"name": "ciclops"})
        view = CreateDatabase()
        view._ec2_conn = mocks.FakeEC2Conn()
        response = view.post(request)
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
        try:
            os.environ["MYSQLAPI_DATABASE_HOST"] = "10.0.1.100"
            request = RequestFactory().post("/", {"name": "plains_of_dawn"})
            view = CreateDatabase()
            view._ec2_conn = mocks.FakeEC2Conn()
            response = view.post(request)
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
        finally:
            db = DatabaseManager("plains_of_dawn")
            db.drop_database()

    def test_create_database_in_a_custom_service_host(self):
        request = RequestFactory().post("/", {"name": "ciclops", "service_host": "127.0.0.1"})
        view = CreateDatabase()
        view._ec2_conn = mocks.FakeEC2Conn()
        response = view.post(request)
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

    def test_ec2_conn_connects_to_ec2_using_data_from_settings_when_not_connected(self):
        fake = mocks.FakeEC2Conn()
        mocker = Mocker()
        r = RegionInfo()
        regioninfo = mocker.replace("boto.ec2.regioninfo.RegionInfo")
        regioninfo(endpoint=settings.EC2_ENDPOINT)
        mocker.result(r)
        connect_ec2 = mocker.replace("boto.connect_ec2")
        connect_ec2(
            aws_access_key_id=settings.EC2_ACCESS_KEY,
            aws_secret_access_key=settings.EC2_SECRET_KEY,
            region=r,
            is_secure=False,
            port=settings.EC2_PORT,
            path=settings.EC2_PATH,
        )
        mocker.result(fake)
        mocker.replay()
        view = CreateDatabase()
        conn = view.ec2_conn
        self.assertIsInstance(conn, mocks.FakeEC2Conn)
        mocker.verify()

    def test_create_database_should_run_instance_using_ami_from_settings(self):
        request = RequestFactory().post("/", {"name": "professor_xavier", "service_host": "127.0.0.1"})
        fake = mocks.FakeEC2Conn()
        view = CreateDatabase()
        view._ec2_conn = fake
        response = view.post(request)
        db = DatabaseManager("professor_xavier")
        db.drop_database()
        self.assertEqual(201, response.status_code, response.content)
        self.assertIn("instance with ami %s and key %s and groups default" % (settings.EC2_AMI, settings.EC2_KEY_NAME), fake.instances)
