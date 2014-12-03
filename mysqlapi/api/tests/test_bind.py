# -*- coding: utf-8 -*-

# Copyright 2013 mysqlapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json

from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory

from mysqlapi.api.database import Connection
from mysqlapi.api.models import DatabaseManager, Instance, canonicalize_db_name
from mysqlapi.api.views import BindApp, BindUnit


class BindAppViewTestCase(TestCase):

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

    def test_bind_app_should_accept_only_post_and_delete(self):
        request = RequestFactory().get("/")
        response = BindApp.as_view()(request, "name")
        self.assertEqual(405, response.status_code)
        request = RequestFactory().put("/")
        response = BindApp.as_view()(request, "name")
        self.assertEqual(405, response.status_code)

    def test_bind_app_creates_user(self):
        instance = Instance.objects.create(
            name="ciclops",
            host="127.0.0.1",
            ec2_id="i-009",
            state="running",
        )
        try:
            request = RequestFactory().post("/", {"unit-host": "192.168.1.1"})
            response = BindApp.as_view()(request, "ciclops")
            self.assertEqual(201, response.status_code)
            content = json.loads(response.content)
            expected = {
                u"MYSQL_HOST": u"127.0.0.1",
                u"MYSQL_PORT": u"3306",
                u"MYSQL_DATABASE_NAME": "ciclops",
                u"MYSQL_USER": u"ciclops",
                u"MYSQL_PASSWORD": content["MYSQL_PASSWORD"],
            }
            self.assertEqual(expected, content)
            sql = "select User, Host FROM mysql.user " +\
                  "WHERE User='ciclops' AND Host='%'"
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
            self.assertEqual("ciclops", row[0])
        finally:
            db = DatabaseManager("ciclops")
            db.drop_user("ciclops", "192.168.1.1")
            instance.delete()

    def test_bind_app_canonicalizes_database_name(self):
        instance = Instance.objects.create(
            name=canonicalize_db_name("some-db"),
            shared=True,
            state="running",
        )
        settings.SHARED_SERVER = "localhost"
        request = RequestFactory().post("/", {"unit-host": "someurl.com"})
        response = BindApp.as_view()(request, "some-db")
        instance.delete()
        self.assertEqual(201, response.status_code)

    def test_bind_app_in_shared_instance(self):
        settings.SHARED_SERVER = "localhost"
        instance = Instance.objects.create(
            name="inside_out",
            shared=True,
            state="running",
        )
        try:
            request = RequestFactory().post("/", {"unit-host": "192.168.1.10"})
            response = BindApp.as_view()(request, "inside_out")
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
            sql = "select User, Host FROM mysql.user " +\
                  "WHERE User='inside_out' AND Host='%'"
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
            self.assertIsNotNone(row)
        finally:
            db = DatabaseManager("inside_out")
            db.drop_user("inside_out", "192.168.1.10")
            instance.delete()

    def test_bind_app_in_shared_instance_with_public_host(self):
        settings.SHARED_SERVER = "localhost"
        settings.SHARED_SERVER_PUBLIC_HOST = "10.10.10.10"
        instance = Instance.objects.create(
            name="inside_out",
            shared=True,
            state="running",
        )
        try:
            request = RequestFactory().post("/", {"unit-host": "192.168.1.10"})
            response = BindApp.as_view()(request, "inside_out")
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
            sql = "select User, Host FROM mysql.user " +\
                  "WHERE User='inside_out' AND Host='%'"
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
            self.assertIsNotNone(row)
        finally:
            db = DatabaseManager("inside_out")
            db.drop_user("inside_out", "192.168.1.10")
            instance.delete()

    def test_bind_app_returns_404_if_the_instance_does_not_exist(self):
        request = RequestFactory().post("/", {"unit-host": "12.12.12.12"})
        response = BindApp.as_view()(request, "idioglossia")
        self.assertEqual(404, response.status_code)
        self.assertEqual("Instance not found", response.content)

    def test_bind_app_gives_precondition_failed_for_pending_instances(self):
        instance = Instance.objects.create(
            name="morning_on_earth",
            host="127.0.0.1",
            ec2_id="i-009",
            state="pending",
        )
        try:
            request = RequestFactory().post("/", {"unit-host": "192.168.1.1"})
            response = BindApp.as_view()(request, "morning_on_earth")
            self.assertEqual(412, response.status_code)
            msg = u"You can't bind to this instance because it's not running."
            self.assertEqual(msg, response.content)
        finally:
            instance.delete()

    def test_unbind_app_should_return_500_and_error_msg_in_body(self):
        instance = Instance.objects.create(name="fails", host="127.0.0.1")
        try:
            request = RequestFactory().delete("/")
            response = BindApp.as_view()(request, "fails")
            self.assertEqual(500, response.status_code)
            content = "Operation DROP USER failed for 'fails'@'%'"
            self.assertEqual(content, response.content)
        finally:
            instance.delete()

    def test_unbind_app_drops_the_user(self):
        instance = Instance.objects.create(name="ciclops", host="127.0.0.1")
        try:
            db = DatabaseManager("ciclops")
            db.create_user("ciclops", "localhost")

            request = RequestFactory().delete("/ciclops")
            response = BindApp.as_view()(request, "ciclops")
            self.assertEqual(200, response.status_code)

            sql = "select User, Host FROM mysql.user " +\
                  "WHERE User='ciclops' AND Host='%'"
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
            self.assertFalse(row)
        finally:
            instance.delete()

    def test_unbind_app_drops_the_user_on_shared_instance(self):
        settings.SHARED_SERVER = "127.0.0.1"
        instance = Instance.objects.create(name="used", shared=True)
        try:
            db = DatabaseManager("used")
            db.create_user("used", "127.0.0.1")
            request = RequestFactory().delete("/used")
            response = BindApp.as_view()(request, "used")
            self.assertEqual(200, response.status_code)
            sql = "select User, Host FROM mysql.user " +\
                  "WHERE User='used' AND Host='%'"
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
            self.assertIsNone(row)
        finally:
            instance.delete()

    def test_unbind_app_return_404_if_the_instance_does_not_exist(self):
        request = RequestFactory().delete("/ciclops")
        response = BindApp.as_view()(request, "ciclops")
        self.assertEqual(404, response.status_code)
        self.assertEqual("Instance not found.", response.content)


class BindUnitTestCase(TestCase):

    def test_post(self):
        request = RequestFactory().post("/")
        response = BindUnit.as_view()(request, "name")
        self.assertEqual(201, response.status_code)

    def test_delete(self):
        request = RequestFactory().delete("/")
        response = BindUnit.as_view()(request, "name")
        self.assertEqual(200, response.status_code)
