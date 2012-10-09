# -*- coding: utf-8 -*-
import json

from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory

from mysqlapi.api.database import Connection
from mysqlapi.api.models import DatabaseManager, Instance
from mysqlapi.api.views import CreateUser


class CreateUserViewTestCase(TestCase):

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
        self.old_shared_server_public_host = settings.SHARED_SERVER_PUBLIC_HOST
        settings.SHARED_SERVER = None
        settings.SHARED_SERVER_PUBLIC_HOST = None

    def tearDown(self):
        settings.SHARED_SERVER = self.old_shared_server
        settings.SHARED_SERVER_PUBLIC_HOST = self.old_shared_server_public_host

    def test_create_user_should_returns_500_when_hostname_is_missing(self):
        request = RequestFactory().post("/", {})
        response = CreateUser.as_view()(request, "database")
        self.assertEqual(500, response.status_code)
        self.assertEqual("Hostname is missing", response.content)

    def test_create_user_should_returns_500_when_hostname_name_is_blank(self):
        request = RequestFactory().post("/", {"hostname": ""})
        response = CreateUser.as_view()(request, "database")
        self.assertEqual(500, response.status_code)
        self.assertEqual("Hostname is empty", response.content)

    def test_create_user_should_returns_405_when_method_is_not_post(self):
        request = RequestFactory().get("/")
        response = CreateUser.as_view()(request, "name")
        self.assertEqual(405, response.status_code)
        request = RequestFactory().put("/")
        response = CreateUser.as_view()(request, "name")
        self.assertEqual(405, response.status_code)
        request = RequestFactory().delete("/")
        response = CreateUser.as_view()(request, "name")
        self.assertEqual(405, response.status_code)

    def test_create_user(self):
        instance = Instance.objects.create(
            name="ciclops",
            host="127.0.0.1",
            ec2_id="i-009",
            state="running",
        )
        try:
            request = RequestFactory().post("/", {"hostname": "192.168.1.1"})
            response = CreateUser.as_view()(request, "ciclops")
            self.assertEqual(201, response.status_code)
            content = json.loads(response.content)
            expected = {
                u"MYSQL_HOST": u"127.0.0.1",
                u"MYSQL_PORT": u"3306",
                u"MYSQL_DATABASE_NAME": "ciclops",
                u"MYSQL_USER": u"ciclops",
                u"MYSQL_PASSWORD": content["MYSQL_PASSWORD"],
            }
            self.assertDictEqual(expected, content)
            self.cursor.execute("select User, Host FROM mysql.user WHERE User='ciclops' AND Host='192.168.1.1'")
            row = self.cursor.fetchone()
            self.assertEqual("ciclops", row[0])
            self.assertEqual("192.168.1.1", row[1])
        finally:
            db = DatabaseManager("ciclops")
            db.drop_user("ciclops", "192.168.1.1")
            instance.delete()

    def test_create_user_should_successed_with_dashed_separated_database_name(self):
        instance = Instance.objects.create(
            name="some-db",
            shared=True,
            state="running",
        )
        settings.SHARED_SERVER = "localhost"
        request = RequestFactory().post("/", {"hostname": "someurl.com"})
        response = CreateUser.as_view()(request, "some-db")
        instance.delete()
        self.assertEqual(201, response.status_code)

    def test_create_user_should_successed_with_dashed_separated_hostname(self):
        instance = Instance.objects.create(
            name="some_db",
            shared=True,
            state="running",
        )
        settings.SHARED_SERVER = "localhost"
        request = RequestFactory().post("/", {"hostname": "some-ec2-url.com"})
        response = CreateUser.as_view()(request, "some_db")
        instance.delete()
        self.assertEqual(201, response.status_code)

    def test_create_user_in_shared_instance(self):
        settings.SHARED_SERVER = "localhost"
        instance = Instance.objects.create(
            name="inside_out",
            shared=True,
            state="running",
        )
        try:
            request = RequestFactory().post("/", {"hostname": "192.168.1.10"})
            response = CreateUser.as_view()(request, "inside_out")
            self.assertEqual(201, response.status_code)
            content = json.loads(response.content)
            expected = {
                u"MYSQL_HOST": u"localhost",
                u"MYSQL_PORT": u"3306",
                u"MYSQL_DATABASE_NAME": "inside_out",
                u"MYSQL_USER": u"inside_out",
                u"MYSQL_PASSWORD": content["MYSQL_PASSWORD"],
            }
            self.assertEqual(expected, content)
            self.cursor.execute("select User, Host FROM mysql.user WHERE User='inside_out' AND Host='192.168.1.10'")
            row = self.cursor.fetchone()
            self.assertIsNotNone(row)
        finally:
            db = DatabaseManager("inside_out")
            db.drop_user("inside_out", "192.168.1.10")
            instance.delete()

    def test_create_user_in_shared_instance_with_public_host(self):
        settings.SHARED_SERVER = "localhost"
        settings.SHARED_SERVER_PUBLIC_HOST = "10.10.10.10"
        instance = Instance.objects.create(
            name="inside_out",
            shared=True,
            state="running",
        )
        try:
            request = RequestFactory().post("/", {"hostname": "192.168.1.10"})
            response = CreateUser.as_view()(request, "inside_out")
            self.assertEqual(201, response.status_code)
            content = json.loads(response.content)
            expected = {
                u"MYSQL_HOST": u"10.10.10.10",
                u"MYSQL_PORT": u"3306",
                u"MYSQL_DATABASE_NAME": "inside_out",
                u"MYSQL_USER": u"inside_out",
                u"MYSQL_PASSWORD": content["MYSQL_PASSWORD"],
            }
            self.assertEqual(expected, content)
            self.cursor.execute("select User, Host FROM mysql.user WHERE User='inside_out' AND Host='192.168.1.10'")
            row = self.cursor.fetchone()
            self.assertIsNotNone(row)
        finally:
            db = DatabaseManager("inside_out")
            db.drop_user("inside_out", "192.168.1.10")
            instance.delete()

    def test_create_user_returns_404_if_the_instance_does_not_exist(self):
        request = RequestFactory().post("/", {"hostname": "12.12.12.12"})
        response = CreateUser.as_view()(request, "idioglossia")
        self.assertEqual(404, response.status_code)
        self.assertEqual("Instance not found", response.content)

    def test_create_user_returns_precondition_failed_if_the_instance_is_pending(self):
        instance = Instance.objects.create(
            name="morning_on_earth",
            host="127.0.0.1",
            ec2_id="i-009",
            state="pending",
        )
        try:
            request = RequestFactory().post("/", {"hostname": "192.168.1.1"})
            response = CreateUser.as_view()(request, "morning_on_earth")
            self.assertEqual(412, response.status_code)
            self.assertEqual(u"You can't bind to this instance because it's not running.", response.content)
        finally:
            instance.delete()
