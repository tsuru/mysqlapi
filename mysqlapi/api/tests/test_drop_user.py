# -*- coding: utf-8 -*-
from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory

from mysqlapi.api.database import Connection
from mysqlapi.api.models import DatabaseManager, Instance
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

    def setUp(self):
        self.old_shared_server = settings.SHARED_SERVER
        settings.SHARED_SERVER = None

    def tearDown(self):
        settings.SHARED_SERVER = self.old_shared_server

    def test_drop_should_return_500_and_error_msg_in_body(self):
        instance = Instance.objects.create(name="fails", host="127.0.0.1")
        try:
            request = RequestFactory().delete("/")
            response = drop_user(request, "fails", "hostname")
            self.assertEqual(500, response.status_code)
            self.assertEqual("Operation DROP USER failed for 'fails'@'hostname'", response.content)
        finally:
            instance.delete()

    def test_drop_should_return_405_when_method_is_not_delete(self):
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
        instance = Instance.objects.create(name="ciclops", host="127.0.0.1")
        try:
            db = DatabaseManager("ciclops")
            db.create_user("ciclops", "localhost")

            request = RequestFactory().delete("/ciclops")
            response = drop_user(request, "ciclops", "localhost")
            self.assertEqual(200, response.status_code)

            self.cursor.execute("select User, Host FROM mysql.user WHERE User='ciclops' AND Host='localhost'")
            row = self.cursor.fetchone()
            self.assertFalse(row)
        finally:
            instance.delete()

    def test_drop_user_from_shared_instance(self):
        settings.SHARED_SERVER = "127.0.0.1"
        instance = Instance.objects.create(name="used", shared=True)
        try:
            db = DatabaseManager("used")
            db.create_user("used", "127.0.0.1")
            request = RequestFactory().delete("/used")
            response = drop_user(request, "used", "127.0.0.1")
            self.assertEqual(200, response.status_code)
            self.cursor.execute("select User, Host FROM mysql.user WHERE User='used' AND Host='127.0.0.1'")
            row = self.cursor.fetchone()
            self.assertIsNone(row)
        finally:
            instance.delete()

    def test_drop_user_return_404_if_the_instance_does_not_exist(self):
        request = RequestFactory().delete("/ciclops")
        response = drop_user(request, "ciclops", "localhost")
        self.assertEqual(404, response.status_code)
        self.assertEqual("Instance not found.", response.content)
