# -*- coding: utf-8 -*-
import time
import unittest

from django.conf import settings
from django.test.client import RequestFactory
from mocker import Mocker

from mysqlapi.api.creator import _instance_queue, reset_queue, set_model, start_creator
from mysqlapi.api.database import Connection
from mysqlapi.api.models import create_database, DatabaseManager, DatabaseCreationException, Instance, InstanceAlreadyExists, InvalidInstanceName
from mysqlapi.api.tests import mocks
from mysqlapi.api.views import CreateDatabase


class CreateDatabaseViewTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = Connection(hostname="localhost", username="root")
        cls.conn.open()
        cls.cursor = cls.conn.cursor()
        cls.old_poll_interval = settings.EC2_POLL_INTERVAL
        settings.EC2_POLL_INTERVAL = 0
        set_model(Instance)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        settings.EC2_POLL_INTERVAL = cls.old_poll_interval
        _instance_queue.close()

    def setUp(self):
        self.old_shared_server = settings.SHARED_SERVER
        settings.SHARED_SERVER = None
        reset_queue()

    def tearDown(self):
        settings.SHARED_SERVER = self.old_shared_server

    def test_create_database_should_returns_500_when_name_is_missing(self):
        request = RequestFactory().post("/", {})
        view = CreateDatabase()
        view._client = mocks.FakeEC2Client()
        response = view.post(request)
        self.assertEqual(500, response.status_code)
        self.assertEqual("App name is missing", response.content)

    def test_create_database_should_returns_500_when_name_is_blank(self):
        request = RequestFactory().post("/", {"name": ""})
        view = CreateDatabase()
        view._client = mocks.FakeEC2Client()
        response = view.post(request)
        self.assertEqual(500, response.status_code)
        self.assertEqual("App name is empty", response.content)

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

    def test_create_database_ec2(self):
        try:
            client = mocks.FakeEC2Client()
            t = start_creator(DatabaseManager, client)
            request = RequestFactory().post("/", {"name": "ciclops"})
            view = CreateDatabase()
            view._client = client
            response = view.post(request)
            self.assertEqual(201, response.status_code)
            self.assertEqual("", response.content)
            t.stop()
            self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'ciclops'")
            row = self.cursor.fetchone()
            self.assertEqual("ciclops", row[0])
        finally:
            db = DatabaseManager("ciclops")
            db.drop_database()

    def test_create_database_should_call_run_from_client(self):
        try:
            cli = mocks.FakeEC2Client()
            t = start_creator(DatabaseManager, cli)
            request = RequestFactory().post("/", {"name": "bowl", "service_host": "127.0.0.1"})
            view = CreateDatabase()
            view._client = cli
            response = view.post(request)
            t.stop()
            self.assertEqual(201, response.status_code)
            self.assertIn("run instance bowl", cli.actions)
        finally:
            self.cursor.execute("DROP DATABASE IF EXISTS bowl")

    def test_create_database_function_sends_the_instance_in_the_creator_queue(self):
        instance = Instance(
            ec2_id="i-00009",
            name="der_trommler",
            host="127.0.0.1",
            state="running",
        )
        ec2_client = mocks.MultipleFailureEC2Client(times=0)
        try:
            t = start_creator(DatabaseManager, ec2_client)
            create_database(instance, ec2_client)
            t.stop()
            self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'der_trommler'")
            row = self.cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual("der_trommler", row[0])
            self.assertIsNotNone(instance.pk)
        finally:
            self.cursor.execute("DROP DATABASE IF EXISTS der_trommler")
            instance.delete()

    def test_create_database_function_raises_exception_if_instance_fail_to_boot(self):
        instance = Instance(name="seven_cities")
        ec2_client = mocks.FakeEC2Client()
        ec2_client.run = lambda instance: False
        with self.assertRaises(DatabaseCreationException) as e:
            create_database(instance, ec2_client)
        self.assertEqual(u"Failed to create EC2 instance.", e.exception[1])

    def test_create_database_terminates_the_instance_if_it_fails_to_create_the_database_and_save_instance_with_error_state(self):
        exc_msg = u"I've failed to create your database, sorry! :("
        mocker = Mocker()
        c_database = mocker.replace("mysqlapi.api.models.DatabaseManager.create_database")
        c_database()
        mocker.throw(Exception(exc_msg))
        mocker.replay()
        instance = Instance(
            ec2_id="i-00009",
            name="home",
            host="unknown.host",
            state="running",
        )
        ec2_client = mocks.FakeEC2Client()
        try:
            t = start_creator(DatabaseManager, ec2_client)
            create_database(instance, ec2_client)
            t.stop()
            self.assertIn("unauthorize instance home", ec2_client.actions)
            self.assertIn("terminate instance home", ec2_client.actions)
            index_unauthorize = ec2_client.actions.index("unauthorize instance home")
            index_terminate = ec2_client.actions.index("terminate instance home")
            assert index_unauthorize < index_terminate, "Should unauthorize before terminate."
            self.assertIsNotNone(instance.pk)
            self.assertEqual("error", instance.state)
            self.assertEqual(exc_msg, instance.reason)
        finally:
            instance.delete()
        mocker.verify()
        mocker.reset()

    def test_create_database_should_authorize_access_to_the_instance(self):
        try:
            cli = mocks.FakeEC2Client()
            t = start_creator(DatabaseManager, cli)
            request = RequestFactory().post("/", {"name": "entre_nous", "service_host": "127.0.0.1"})
            view = CreateDatabase()
            view._client = cli
            response = view.post(request)
            t.stop()
            self.assertEqual(201, response.status_code)
            self.assertIn("authorize instance entre_nous", cli.actions)
        finally:
            self.cursor.execute("DROP DATABASE IF EXISTS entre_nous")

    def test_create_database_terminates_the_instance_if_it_fails_to_authorize_and_save_instance_with_error_state(self):
        instance = Instance(
            ec2_id="i-00009",
            name="home",
            host="unknown.host",
            state="running",
        )
        ec2_client = mocks.FakeEC2Client()
        ec2_client.authorize = lambda *args, **kwargs: False
        try:
            t = start_creator(DatabaseManager, ec2_client)
            create_database(instance, ec2_client)
            t.stop()
            self.assertIn("terminate instance home", ec2_client.actions)
            self.assertIsNotNone(instance.pk)
            self.assertEqual("error", instance.state)
            self.assertEqual("Failed to authorize access to the instance.", instance.reason)
        finally:
            instance.delete()

    def test_create_database_shared(self):
        settings.SHARED_SERVER = "127.0.0.1"
        instance = Instance(
            name="water",
            ec2_id="i-681"
        )
        try:
            create_database(instance)
            self.cursor.execute("select SCHEMA_NAME from information_schema.SCHEMATA where SCHEMA_NAME = 'water'")
            row = self.cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual("water", row[0])
            self.assertIsNotNone(instance.pk)
            self.assertTrue(instance.shared)
            self.assertEqual("running", instance.state)
            self.assertIsNone(instance.ec2_id)
        finally:
            self.cursor.execute("DROP DATABASE IF EXISTS water")
            instance.delete()

    def test_create_database_when_instance_already_exist(self):
        self.cursor.execute("CREATE DATABASE caravan")
        settings.SHARED_SERVER = "127.0.0.1"
        instance = Instance(
            name="caravan",
            ec2_id="i-89",
        )
        instance.save()
        try:
            with self.assertRaises(InstanceAlreadyExists):
                create_database(instance)
        finally:
            self.cursor.execute("DROP DATABASE caravan")

    # protecting against incosistency between the api database and mysql server
    # itself
    def test_create_database_when_database_already_exist(self):
        self.cursor.execute("CREATE DATABASE caravan")
        settings.SHARED_SERVER = "127.0.0.1"
        instance = Instance(
            name="caravan",
            ec2_id="i-89",
        )
        try:
            with self.assertRaises(InstanceAlreadyExists):
                create_database(instance)
        finally:
            self.cursor.execute("DROP DATABASE caravan")
            if instance.pk:
                instance.delete()

    def test_create_database_invalid_name(self):
        instance = Instance(name="mysql")
        with self.assertRaises(InvalidInstanceName):
            create_database(instance)
