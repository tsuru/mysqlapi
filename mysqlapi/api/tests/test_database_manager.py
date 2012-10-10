# -*- coding: utf-8 -*-
from django.test import TestCase

from mysqlapi.api.database import Connection
from mysqlapi.api.models import DatabaseManager


class DatabaseTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = Connection(hostname="localhost", username="root")
        cls.conn.open()
        cls.cursor = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_create_database_with_custom_hostname(self):
        db = DatabaseManager("newdatabase", host="127.0.0.1")
        db.create_database()
        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'newdatabase'")
        row = self.cursor.fetchone()
        self.assertEqual("newdatabase", row[0])
        db.drop_database()

    def test_create(self):
        db = DatabaseManager("newdatabase")
        db.create_database()
        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'newdatabase'")
        row = self.cursor.fetchone()
        self.assertEqual("newdatabase", row[0])
        db.drop_database()

    def test_drop(self):
        db = DatabaseManager("otherdatabase")
        db.create_database()
        db.drop_database()
        self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'otherdatabase'")
        row = self.cursor.fetchone()
        self.assertFalse(row)

    def test_create_user(self):
        db = DatabaseManager("wolverine")
        db.create_user("wolverine", "%")
        self.cursor.execute("select User, Host FROM mysql.user WHERE User='wolverine' AND Host='%'")
        row = self.cursor.fetchone()
        self.assertEqual("wolverine", row[0])
        self.assertEqual("%", row[1])
        db.drop_user("wolverine", "%")

    def test_create_user_should_generate_an_username_when_username_length_is_greater_than_16(self):
        db = DatabaseManager("usernamegreaterthan16")
        username, password = db.create_user("usernamegreaterthan16", "%")
        self.cursor.execute("select User, Host FROM mysql.user WHERE User like 'usernamegrea%' AND Host='%'")
        row = self.cursor.fetchone()
        self.assertEqual("usernamegrea", row[0][:12])
        db = DatabaseManager(row[0])
        db.drop_user(username, "%")

    def test_drop_user(self):
        db = DatabaseManager("magneto")
        db.create_user("magneto", "%")
        db.drop_user("magneto", "%")
        self.cursor.execute("select User, Host FROM mysql.user WHERE User='wolverine' AND Host='%'")
        row = self.cursor.fetchone()
        self.assertFalse(row)

    def test_export(self):
        db = DatabaseManager("magneto")
        db.create_database()
        db.create_user("magneto", "%")
        self.cursor.execute("create table magneto.foo ( test varchar(255) );")
        expected = """/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `foo` (
  `test` varchar(255) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
"""
        result = db.export()
        self.assertEqual(expected, result.replace("InnoDB", "MyISAM"))
        db.drop_database()
        db.drop_user("magneto", "%")

    def test_is_up_return_True_if_everything_is_ok_with_the_connection(self):
        db = DatabaseManager("wolverine")
        self.assertTrue(db.is_up())

    def test_is_up_return_False_something_is_not_ok_with_the_connection(self):
        db = DatabaseManager("wolverine", host="unknownhost.absolute.impossibru.moc")
        self.assertFalse(db.is_up())

    def test_public_host_is_host_when_private_attribute_is_None(self):
        db = DatabaseManager("wolverine", host="localhost")
        self.assertEqual(db.host, db.public_host)

    def test_public_host_is_the_value_of_the_private_attribute_when_it_is_defined(self):
        db = DatabaseManager("wolverine", host="localhost", public_host="10.10.10.10")
        self.assertEqual(db._public_host, db.public_host)
