# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.client import RequestFactory

from mysqlapi.api.database import Connection
from mysqlapi.api.models import DatabaseManager
from mysqlapi.api.views import drop_user


class DropUserViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = Connection(hostname="localhost", username="root")
        cls.conn.open()
        cls.cursor = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_drop_should_returns_500_and_error_msg_in_body(self):
        request = RequestFactory().delete("/")
        response = drop_user(request, "doesnotexists", "hostname")
        self.assertEqual(500, response.status_code)
        self.assertEqual("Operation DROP USER failed for 'doesnotexists'@'hostname'", response.content)

    def test_drop_should_returns_405_when_method_is_not_delete(self):
        request = RequestFactory().get("/")
        response = drop_user(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().put("/")
        response = drop_user(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().post("/")
        response = drop_user(request)
        self.assertEqual(405, response.status_code)

    def test_drop_user(self):
        db = DatabaseManager("ciclops")
        db.create_user("ciclops", "localhost")

        request = RequestFactory().delete("/ciclops")
        response = drop_user(request, "ciclops", "localhost")
        self.assertEqual(204, response.status_code)

        self.cursor.execute("select User, Host FROM mysql.user WHERE User='ciclops' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertFalse(row)

    def test_drop_user_fom_custom_service_host(self):
        db = DatabaseManager("ciclops", "127.0.0.1")
        db.create_user("ciclops", "localhost")

        request = RequestFactory().delete("/ciclops", {"service_host": "127.0.0.1"})
        response = drop_user(request, "ciclops", "localhost")
        self.assertEqual(204, response.status_code)

        self.cursor.execute("select User, Host FROM mysql.user WHERE User='ciclops' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertFalse(row)
