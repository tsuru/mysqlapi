# -*- coding: utf-8 -*-
import hashlib
import unittest
import mock

from django.conf import settings
from django.db.models import BooleanField, CharField
from django.test import TestCase

from mysqlapi.api.models import DatabaseManager, Instance, canonicalize_db_name


class DatabaseManagerTestCase(unittest.TestCase):

    def test_init_should_canonicalize_name_property(self):
        db = DatabaseManager(
            name="foo-bar",
            host=settings.SHARED_SERVER,
            user=settings.SHARED_USER,
            password=settings.SHARED_PASSWORD,
        )
        self.assertRegexpMatches(db.name, "^foo_bar.*$")


class InstanceTestCase(TestCase):

    def setUp(self):
        self.old_shared_server = settings.SHARED_SERVER
        settings.SHARED_SERVER = None
        self.old_shared_user = settings.SHARED_USER
        self.old_shared_password = settings.SHARED_PASSWORD
        self.old_shared_server_public_host = settings.SHARED_SERVER_PUBLIC_HOST

    def tearDown(self):
        settings.SHARED_SERVER = self.old_shared_server
        settings.SHARED_USER = self.old_shared_user
        settings.SHARED_PASSWORD = self.old_shared_password
        settings.SHARED_SERVER_PUBLIC_HOST = self.old_shared_server_public_host

    def test_instance_should_have_a_name(self):
        self.assertIn("name", Instance._meta.get_all_field_names())

    def test_instance_name_should_be_CharField(self):
        field = Instance._meta.get_field_by_name("name")[0]
        self.assertIsInstance(field, CharField)

    def test_instance_name_should_have_at_most_100_characters(self):
        field = Instance._meta.get_field_by_name("name")[0]
        self.assertEqual(100, field.max_length)

    def test_instance_name_should_be_unique(self):
        field = Instance._meta.get_field_by_name("name")[0]
        self.assertTrue(field.unique)

    def test_instance_should_have_an_ec2_id(self):
        self.assertIn("ec2_id", Instance._meta.get_all_field_names())

    def test_ec2_id_should_be_CharField(self):
        field = Instance._meta.get_field_by_name("ec2_id")[0]
        self.assertIsInstance(field, CharField)

    def test_ec2_id_should_have_at_most_100_characters(self):
        field = Instance._meta.get_field_by_name("ec2_id")[0]
        self.assertEqual(100, field.max_length)

    def test_ec2_id_should_accept_null_and_empty_values(self):
        field = Instance._meta.get_field_by_name("ec2_id")[0]
        self.assertTrue(field.blank)
        self.assertTrue(field.null)

    def test_instance_should_have_an_state(self):
        self.assertIn("state", Instance._meta.get_all_field_names())

    def test_state_should_be_CharField(self):
        field = Instance._meta.get_field_by_name("state")[0]
        self.assertIsInstance(field, CharField)

    def test_state_should_have_at_most_50_characters(self):
        field = Instance._meta.get_field_by_name("state")[0]
        self.assertEqual(50, field.max_length)

    def test_state_should_be_pending_by_default(self):
        field = Instance._meta.get_field_by_name("state")[0]
        self.assertEqual("pending", field.default)

    def test_state_should_have_choices(self):
        expected = (
            ("pending", "pending"),
            ("running", "running"),
            ("error", "error"),
        )
        field = Instance._meta.get_field_by_name("state")[0]
        self.assertEqual(expected, field.choices)

    def test_instance_should_have_a_host(self):
        self.assertIn("host", Instance._meta.get_all_field_names())

    def test_host_should_be_CharField(self):
        field = Instance._meta.get_field_by_name("host")[0]
        self.assertIsInstance(field, CharField)

    def test_host_should_have_at_most_50_characters(self):
        field = Instance._meta.get_field_by_name("host")[0]
        self.assertEqual(50, field.max_length)

    def test_host_should_accept_empty_values(self):
        field = Instance._meta.get_field_by_name("host")[0]
        self.assertTrue(field.blank)

    def test_host_should_accept_null_values(self):
        field = Instance._meta.get_field_by_name("host")[0]
        self.assertTrue(field.null)

    def test_instance_should_have_a_port(self):
        self.assertIn("port", Instance._meta.get_all_field_names())

    def test_port_should_be_a_CharField(self):
        field = Instance._meta.get_field_by_name("port")[0]
        self.assertIsInstance(field, CharField)

    def test_port_should_have_at_most_5_characters(self):
        field = Instance._meta.get_field_by_name("port")[0]
        self.assertEqual(5, field.max_length)

    def test_port_default_value_should_be_3306(self):
        field = Instance._meta.get_field_by_name("port")[0]
        self.assertEqual("3306", field.default)

    def test_instance_should_have_reason_of_failure(self):
        self.assertIn("reason", Instance._meta.get_all_field_names())

    def test_reason_should_be_CharField(self):
        field = Instance._meta.get_field_by_name("reason")[0]
        self.assertIsInstance(field, CharField)

    def test_reason_should_have_at_most_1000_characters(self):
        field = Instance._meta.get_field_by_name("reason")[0]
        self.assertEqual(1000, field.max_length)

    def test_reason_should_accept_null_values(self):
        field = Instance._meta.get_field_by_name("reason")[0]
        self.assertTrue(field.null)

    def test_reason_should_accept_blank(self):
        field = Instance._meta.get_field_by_name("reason")[0]
        self.assertTrue(field.blank)

    def test_reason_should_have_None_as_default_value(self):
        field = Instance._meta.get_field_by_name("reason")[0]
        self.assertEqual(None, field.default)

    def test_instance_should_have_a_shared_flag(self):
        self.assertIn("shared", Instance._meta.get_all_field_names())

    def test_shared_should_be_a_boolean_field(self):
        field = Instance._meta.get_field_by_name("shared")[0]
        self.assertIsInstance(field, BooleanField)

    def test_shared_should_be_False_by_default(self):
        field = Instance._meta.get_field_by_name("shared")[0]
        self.assertEqual(False, field.default)

    def test_is_up_returns_true_when_instance_is_running_and_db_is_up(self):
        with mock.patch("mysqlapi.api.models.DatabaseManager.is_up") as is_up:
            is_up.return_value = True
            instance = Instance(name="foo", state="running")
            self.assertTrue(instance.is_up())

    def test_is_up_should_return_false_when_instance_is_not_running(self):
        with mock.patch("mysqlapi.api.models.DatabaseManager.is_up") as is_up:
            is_up.return_value = False
            instance = Instance(name="foo", state="running")
            self.assertFalse(instance.is_up())

    def test_db_manager_dedicated_instance(self):
        instance = Instance(
            host="10.10.10.10",
            shared=False,
        )
        db = instance.db_manager()
        self.assertIsInstance(db, DatabaseManager)
        self.assertEqual(instance.host, db.conn.hostname)
        self.assertEqual("root", db.conn.username)
        self.assertEqual("", db.conn.password)

    def test_db_manager_shared_instance(self):
        settings.SHARED_SERVER = "20.20.20.20"
        settings.SHARED_USER = "fsouza"
        settings.SHARED_PASSWORD = "123"
        instance = Instance(
            shared=True,
        )
        db = instance.db_manager()
        self.assertIsInstance(db, DatabaseManager)
        self.assertEqual("20.20.20.20", db.conn.hostname)
        self.assertEqual("fsouza", db.conn.username)
        self.assertEqual("123", db.conn.password)

    def test_db_manager_shared_instance_with_public_shared(self):
        settings.SHARED_SERVER = "20.20.20.20"
        settings.SHARED_SERVER_PUBLIC_HOST = "10.10.10.10"
        settings.SHARED_USER = "fsouza"
        settings.SHARED_PASSWORD = "123"
        instance = Instance(shared=True)
        db = instance.db_manager()
        self.assertEqual("10.10.10.10", db.public_host)


class CanonicalizeTestCase(unittest.TestCase):

    def test_canonicalize_db_name_dont_change_strings_without_dashes(self):
        canonicalized_name = canonicalize_db_name("foo_bar")
        self.assertEqual("foo_bar", canonicalized_name)

    def test_canonicalize_db_name_replaces_dashes_with_underline(self):
        canonicalized_name = canonicalize_db_name("foo-bar")
        expected = "foo_bar{0}".\
                   format(hashlib.sha1("foo-bar").hexdigest()[:10])
        self.assertEqual(canonicalized_name, expected)

    def test_canonicalize_db_name_replaces_whitespaces_with_underline(self):
        canonicalized_name = canonicalize_db_name(" foo ")
        expected = "_foo_{0}".format(hashlib.sha1(" foo ").hexdigest()[:10])
        self.assertEqual(canonicalized_name, expected)

    def test_canonicalize_db_name_do_nothing_when_called_twice(self):
        canonicalized_name = canonicalize_db_name(
            canonicalize_db_name(" foo ")
        )
        expected = "_foo_{0}".format(hashlib.sha1(" foo ").hexdigest()[:10])
        self.assertEqual(canonicalized_name, expected)
