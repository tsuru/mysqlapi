from django.test import TestCase
from django.db import connection
from django.test.client import RequestFactory
from django.utils import simplejson
from django.test.utils import override_settings

from mysqlapi.api.models import DatabaseManager
from mysqlapi.api.views import export, create_user, create_database, drop_user, drop_database


DATABASES_MOCK = {
    'default': {
        'HOST': 'somehost',
    }
}


class CreateDatabaseViewTestCase(TestCase):

    def setUp(self):
        self.cursor = connection.cursor()

    def test_create_database_should_returns_500_when_appname_is_missing(self):
        request = RequestFactory().post("/", {})
        response = create_database(request)
        self.assertEqual(500, response.status_code)
        self.assertEqual("App name is missing", response.content)

    def test_create_database_should_returns_500_when_appname_is_blank(self):
        request = RequestFactory().post("/", {"appname": ""})
        response = create_database(request)
        self.assertEqual(500, response.status_code)
        self.assertEqual("App name is empty", response.content)

    def test_create_database_should_returns_500_and_error_msg_in_body(self):
        db = DatabaseManager("ciclops")
        db.create()
        request = RequestFactory().post("/", {"appname": "ciclops"})
        response = create_database(request)
        self.assertEqual(500, response.status_code)
        self.assertEqual("Can't create database 'ciclops'; database exists", response.content)
        db.drop()

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

    @override_settings(DATABASES=DATABASES_MOCK)
    def test_create_database(self):
        request = RequestFactory().post("/", {"appname": "ciclops"})
        response = create_database(request)
        self.assertEqual(201, response.status_code)
        content = simplejson.loads(response.content)
        expected = {
            u"MYSQL_DATABASE_NAME": u"ciclops",
            u"MYSQL_HOST": u"somehost",
            u"MYSQL_PORT": u"3306",
        }
        self.assertDictEqual(expected, content)

        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'ciclops'")
        row = self.cursor.fetchone()
        self.assertEqual("ciclops", row[0])

        db = DatabaseManager("ciclops")
        db.drop()


class CreateUserViewTestCase(TestCase):

    def setUp(self):
        self.cursor = connection.cursor()

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

    # def test_create_user_should_returns_500_when_database_does_not_exists(self):
    #     request = RequestFactory().post("/", {"hostname": ""})
    #     response = create_user(request, "database")
    #     self.assertEqual(500, response.status_code)
    #     self.assertEqual("Hostname is empty", response.content)

    def test_create_user_should_returns_405_when_method_is_not_post(self):
        request = RequestFactory().get("/")
        response = create_user(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().put("/")
        response = create_user(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().delete("/")
        response = create_user(request)
        self.assertEqual(405, response.status_code)

    @override_settings(DATABASES=DATABASES_MOCK)
    def test_create_user(self):
        request = RequestFactory().post("/", {"hostname": "192.168.1.1"})
        response = create_user(request, "ciclops")
        self.assertEqual(201, response.status_code)
        content = simplejson.loads(response.content)
        expected = {
            u"MYSQL_USER": u"ciclops",
            u"MYSQL_PASSWORD": content["MYSQL_PASSWORD"],
        }
        self.assertDictEqual(expected, content)

        self.cursor.execute("select User, Host FROM mysql.user WHERE User='ciclops' AND Host='192.168.1.1'")
        row = self.cursor.fetchone()
        self.assertEqual("ciclops", row[0])
        self.assertEqual("192.168.1.1", row[1])

        db = DatabaseManager("ciclops", host="192.168.1.1")
        db.drop_user()


class ExportViewTestCase(TestCase):

    def setUp(self):
        self.cursor = connection.cursor()

    def test_export(self):
        db = DatabaseManager("magneto")
        db.create()
        db.create_user()
        self.cursor.execute("create table magneto.foo ( test varchar(255) );")
        expected = """/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `foo` (
  `test` varchar(255) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
"""
        request = RequestFactory().get("/")
        result = export(request, "magneto")
        self.assertEqual(200, result.status_code)
        self.assertEqual(expected, result.content)
        db.drop()
        db.drop_user()

    def test_export_should_returns_500_when_database_does_not_exist(self):
        request = RequestFactory().get("/", {})
        response = export(request, "doesnotexists")
        self.assertEqual(500, response.status_code)
        self.assertEqual("Unknown database 'doesnotexists' when selecting the database", response.content)

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


class DropUserViewTestCase(TestCase):

    def setUp(self):
        self.cursor = connection.cursor()

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
        db = DatabaseManager("ciclops", host="localhost")
        db.create_user()

        request = RequestFactory().delete("/ciclops")
        response = drop_user(request, "ciclops", "localhost")
        self.assertEqual(200, response.status_code)

        self.cursor.execute("select User, Host FROM mysql.user WHERE User='ciclops' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertFalse(row)


class DropDatabaseViewTestCase(TestCase):

    def setUp(self):
        self.cursor = connection.cursor()

    def test_drop_should_returns_500_and_error_msg_in_body(self):
        request = RequestFactory().delete("/")
        response = drop_database(request, "doesnotexists")
        self.assertEqual(500, response.status_code)
        self.assertEqual("Can't drop database 'doesnotexists'; database doesn't exist", response.content)

    def test_drop_should_returns_405_when_method_is_not_delete(self):
        request = RequestFactory().get("/")
        response = drop_database(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().put("/")
        response = drop_database(request)
        self.assertEqual(405, response.status_code)

        request = RequestFactory().post("/")
        response = drop_database(request)
        self.assertEqual(405, response.status_code)

    def test_drop(self):
        db = DatabaseManager("ciclops")
        db.create()

        request = RequestFactory().delete("/ciclops")
        response = drop_database(request, "ciclops")
        self.assertEqual(200, response.status_code)

        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'ciclops'")
        row = self.cursor.fetchone()
        self.assertFalse(row)


class DatabaseTestCase(TestCase):

    def setUp(self):
        self.cursor = connection.cursor()

    def test_create(self):
        db = DatabaseManager("newdatabase")
        db.create()
        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'newdatabase'")
        row = self.cursor.fetchone()
        self.assertEqual("newdatabase", row[0])
        db.drop()

    def test_drop(self):
        db = DatabaseManager("otherdatabase")
        db.create()
        db.drop()
        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'otherdatabase'")
        row = self.cursor.fetchone()
        self.assertFalse(row)

    def test_create_user(self):
        db = DatabaseManager("wolverine")
        db.create_user()
        self.cursor.execute("select User, Host FROM mysql.user WHERE User='wolverine' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertEqual("wolverine", row[0])
        self.assertEqual("localhost", row[1])
        db.drop_user()

    def test_create_user_should_generate_an_username_when_username_length_is_greater_than_16(self):
        db = DatabaseManager("usernamegreaterthan16")
        db.create_user()
        self.cursor.execute("select User, Host FROM mysql.user WHERE User like 'usernamegrea%' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertEqual("usernamegrea", row[0][:12])
        db = DatabaseManager(row[0])
        db.drop_user()

    def test_drop_user(self):
        db = DatabaseManager("magneto")
        db.create_user()
        db.drop_user()
        self.cursor.execute("select User, Host FROM mysql.user WHERE User='wolverine' AND Host='localhost'")
        row = self.cursor.fetchone()
        self.assertFalse(row)

    def test_export(self):
        db = DatabaseManager("magneto")
        db.create()
        db.create_user()
        self.cursor.execute("create table magneto.foo ( test varchar(255) );")
        expected = """/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `foo` (
  `test` varchar(255) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
"""
        result = db.export()
        self.assertEqual(expected, result)
        db.drop()
        db.drop_user()
