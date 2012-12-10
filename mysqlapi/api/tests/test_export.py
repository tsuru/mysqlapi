# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.client import RequestFactory

from mysqlapi.api.database import Connection
from mysqlapi.api.models import DatabaseManager
from mysqlapi.api.views import export


class ExportViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = Connection(hostname="localhost", username="root")
        cls.conn.open()
        cls.cursor = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_export_from_a_custom_service_host(self):
        db = DatabaseManager("magneto", host="127.0.0.1")
        db.create_database()
        db.create_user("magneto", "%")
        self.cursor.execute("create table magneto.foo ( test varchar(255) );")
        expected = """\
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `foo` (
  `test` varchar(255) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
"""
        request = RequestFactory().get("/", {"service_host": "127.0.0.1"})
        result = export(request, "magneto")
        self.assertEqual(200, result.status_code)
        self.assertEqual(expected, result.content.replace("InnoDB", "MyISAM"))
        db.drop_database()
        db.drop_user("magneto", "%")

    def test_export(self):
        db = DatabaseManager("magneto")
        db.create_database()
        db.create_user("magneto", "%")
        self.cursor.execute("create table magneto.foo ( test varchar(255) );")
        expected = """\
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `foo` (
  `test` varchar(255) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
"""
        request = RequestFactory().get("/")
        result = export(request, "magneto")
        self.assertEqual(200, result.status_code)
        self.assertEqual(expected, result.content.replace("InnoDB", "MyISAM"))
        db.drop_database()
        db.drop_user("magneto", "%")

    def test_export_should_returns_500_when_database_does_not_exist(self):
        request = RequestFactory().get("/", {})
        response = export(request, "doesnotexists")
        self.assertEqual(500, response.status_code)
        msg = "Unknown database 'doesnotexists' when selecting the database"
        self.assertEqual(msg, response.content)

    def test_export_should_returns_405_when_method_is_not_get(self):
        request = RequestFactory().post("/")
        response = export(request, "xavier")
        self.assertEqual(405, response.status_code)

        request = RequestFactory().put("/")
        response = export(request, "xavier")
        self.assertEqual(405, response.status_code)

        request = RequestFactory().delete("/")
        response = export(request, "xavier")
        self.assertEqual(405, response.status_code)
