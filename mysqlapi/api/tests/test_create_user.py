# -*- coding: utf-8 -*-
import json

from django.test import TestCase
from django.test.client import RequestFactory

from mysqlapi.api.database import Connection
from mysqlapi.api.models import DatabaseManager
from mysqlapi.api.views import create_user


class CreateUserViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = Connection(hostname="localhost", username="root")
        cls.conn.open()
        cls.cursor = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_create_user_should_returns_500_when_hostname_is_missing(self):
        request = RequestFactory().post("/", {})
        response = create_user(request, "database")
        self.assertEqual(500, response.status_code)
        self.assertEqual("Hostname is missing", response.content)

    def test_create_user_should_returns_500_when_hostname_name_is_blank(self):
        request = RequestFactory().post("/", {"hostname": ""})
        response = create_user(request, "database")
        self.assertEqual(500, response.status_code)
        self.assertEqual("Hostname is empty", response.content)

    def test_create_user_should_returns_405_when_method_is_not_post(self):
        request = RequestFactory().get("/")
        response = create_user(request, "name")
        self.assertEqual(405, response.status_code)

        request = RequestFactory().put("/")
        response = create_user(request, "name")
        self.assertEqual(405, response.status_code)

        request = RequestFactory().delete("/")
        response = create_user(request, "name")
        self.assertEqual(405, response.status_code)

    def test_create_user(self):
        request = RequestFactory().post("/", {"hostname": "192.168.1.1"})
        response = create_user(request, "ciclops")
        self.assertEqual(201, response.status_code)
        content = json.loads(response.content)
        expected = {
            u"MYSQL_USER": u"ciclops",
            u"MYSQL_PASSWORD": content["MYSQL_PASSWORD"],
        }
        self.assertDictEqual(expected, content)

        self.cursor.execute("select User, Host FROM mysql.user WHERE User='ciclops' AND Host='192.168.1.1'")
        row = self.cursor.fetchone()
        self.assertEqual("ciclops", row[0])
        self.assertEqual("192.168.1.1", row[1])

        db = DatabaseManager("ciclops")
        db.drop_user("ciclops", "192.168.1.1")

    def test_create_user_in_a_custom_service_host(self):
        request = RequestFactory().post("/", {"hostname": "192.168.1.1", "service_host": "127.0.0.1"})
        response = create_user(request, "ciclops")
        self.assertEqual(201, response.status_code)
        content = json.loads(response.content)
        expected = {
            u"MYSQL_USER": u"ciclops",
            u"MYSQL_PASSWORD": content["MYSQL_PASSWORD"],
        }
        self.assertDictEqual(expected, content)

        self.cursor.execute("select User, Host FROM mysql.user WHERE User='ciclops' AND Host='192.168.1.1'")
        row = self.cursor.fetchone()
        self.assertEqual("ciclops", row[0])
        self.assertEqual("192.168.1.1", row[1])

        db = DatabaseManager("ciclops")
        db.drop_user("ciclops", "192.168.1.1")
