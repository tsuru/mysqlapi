# -*- coding: utf-8 -*-
import unittest
import mock

from django.conf import settings
from django.test.client import RequestFactory

from mysqlapi.api.creator import (_instance_queue, reset_queue,
                                  set_model, start_creator)
from mysqlapi.api.database import Connection
from mysqlapi.api.models import (create_database, DatabaseManager,
                                 DatabaseCreationException, Instance,
                                 InstanceAlreadyExists, InvalidInstanceName,
                                 canonicalize_db_name)
from mysqlapi.api.tests import mocks
from mysqlapi.api.views import CreateDatabase


class CreateDatabaseViewTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = Connection(hostname="localhost", username="root")
        cls.conn.open()
        cls.old_poll_interval = settings.EC2_POLL_INTERVAL
        settings.EC2_POLL_INTERVAL = 0
        set_model(Instance)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        settings.EC2_POLL_INTERVAL = cls.old_poll_interval
        _instance_queue.close()

    def setUp(self):
        self.cursor = self.conn.cursor()
        self.old_shared_server = settings.SHARED_SERVER
        settings.SHARED_SERVER = None
        reset_queue()

    def tearDown(self):
        settings.SHARED_SERVER = self.old_shared_server
        self.cursor.close()

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
            sql = "select SCHEMA_NAME from information_schema.SCHEMATA " + \
                  "where SCHEMA_NAME = 'ciclops'"
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
            self.assertEqual("ciclops", row[0])
        finally:
            db = DatabaseManager("ciclops")
            db.drop_database()

    def test_create_database_should_call_run_from_client(self):
        try:
            cli = mocks.FakeEC2Client()
            t = start_creator(DatabaseManager, cli)
            data = {"name": "bowl", "service_host": "127.0.0.1"}
            request = RequestFactory().post("/", data)
            view = CreateDatabase()
            view._client = cli
            response = view.post(request)
            t.stop()
            self.assertEqual(201, response.status_code)
            self.assertIn("run instance bowl", cli.actions)
        finally:
            self.cursor.execute("DROP DATABASE IF EXISTS bowl")

    def test_create_database_sends_the_instance_to_the_queue(self):
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
            sql = "select SCHEMA_NAME from information_schema.SCHEMATA " +\
                  "where SCHEMA_NAME = 'der_trommler'"
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual("der_trommler", row[0])
            self.assertIsNotNone(instance.pk)
        finally:
            self.cursor.execute("DROP DATABASE IF EXISTS der_trommler")
            instance.delete()

    def test_create_database_raises_exception_when_instance_fail_to_boot(self):
        instance = Instance(name="seven_cities")
        ec2_client = mocks.FakeEC2Client()
        ec2_client.run = lambda instance: False
        with self.assertRaises(DatabaseCreationException) as e:
            create_database(instance, ec2_client)
        self.assertEqual(u"Failed to create EC2 instance.", e.exception[1])

    def test_create_database_terminates_the_instance_when_cant_create_db(self):
        exc_msg = u"I've failed to create your database, sorry! :("
        module = "mysqlapi.api.models.DatabaseManager.create_database"
        with mock.patch(module) as c_database:
            c_database.side_effect = Exception(exc_msg)
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
                index_unauthorize = ec2_client.actions.index(
                    "unauthorize instance home"
                )
                index_terminate = ec2_client.actions.index(
                    "terminate instance home"
                )
                msg = "Should unauthorize before terminate."
                assert index_unauthorize < index_terminate, msg
                self.assertIsNotNone(instance.pk)
                self.assertEqual("error", instance.state)
                self.assertEqual(exc_msg, instance.reason)
            finally:
                instance.delete()

    def test_create_database_should_authorize_access_to_the_instance(self):
        try:
            cli = mocks.FakeEC2Client()
            t = start_creator(DatabaseManager, cli)
            data = {"name": "entre_nous", "service_host": "127.0.0.1"}
            request = RequestFactory().post("/", data)
            view = CreateDatabase()
            view._client = cli
            response = view.post(request)
            t.stop()
            self.assertEqual(201, response.status_code)
            self.assertIn("authorize instance entre_nous", cli.actions)
        finally:
            self.cursor.execute("DROP DATABASE IF EXISTS entre_nous")

    def test_create_database_canonicalizes_the_name_of_the_database(self):
        settings.SHARED_SERVER = "127.0.0.1"
        request = RequestFactory().post("/", {"name": "foo-bar"})
        response = CreateDatabase().post(request)
        instances_filter = Instance.objects.filter(
            name=canonicalize_db_name("foo-bar")
        )
        exists = instances_filter.exists()
        sql = "DROP DATABASE IF EXISTS {0}"
        self.cursor.execute(sql.format(canonicalize_db_name("foo-bar")))
        instances_filter[0].delete()
        self.assertEqual(201, response.status_code)
        self.assertTrue(exists)


class CreateDatabaseFunctionTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = Connection(hostname="localhost", username="root")
        cls.conn.open()
        cls.old_poll_interval = settings.EC2_POLL_INTERVAL
        settings.EC2_POLL_INTERVAL = 0
        set_model(Instance)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        settings.EC2_POLL_INTERVAL = cls.old_poll_interval
        _instance_queue.close()

    def setUp(self):
        self.cursor = self.conn.cursor()
        self.old_shared_server = settings.SHARED_SERVER
        settings.SHARED_SERVER = None
        reset_queue()

    def tearDown(self):
        settings.SHARED_SERVER = self.old_shared_server
        self.cursor.close()

    def test_create_database_terminates_the_instance_when_cant_authorize(self):
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
            reason = "Failed to authorize access to the instance."
            self.assertEqual(reason, instance.reason)
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
            sql = "select SCHEMA_NAME from information_schema.SCHEMATA " +\
                  "where SCHEMA_NAME = 'water'"
            self.cursor.execute(sql)
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

    def test_create_database_canonicalizes_name(self):
        settings.SHARED_SERVER = "127.0.0.1"
        instance = Instance(
            name="invalid-db-name",
            ec2_id="i-681"
        )
        canonical_name = canonicalize_db_name(instance.name)
        try:
            create_database(instance)
            sql = "select SCHEMA_NAME from information_schema.SCHEMATA " +\
                  "where SCHEMA_NAME = '{0}'"
            self.cursor.execute(sql.format(canonical_name))
            row = self.cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(canonical_name, row[0])
            self.assertIsNotNone(instance.pk)
        finally:
            sql = "DROP DATABASE IF EXISTS {0}"
            self.cursor.execute(sql.format(canonical_name))
            instance.delete()

    def test_create_database_when_instance_already_exist(self):
        settings.SHARED_SERVER = "127.0.0.1"
        instance = Instance(
            name="caravanx",
            ec2_id="i-89",
        )
        instance.save()
        try:
            with self.assertRaises(InstanceAlreadyExists):
                create_database(instance)
        finally:
            instance.delete()
            self.cursor.execute("DROP DATABASE IF EXISTS caravanx")

    # protecting against incosistency between the api database and mysql server
    # itself
    def test_create_database_when_database_already_exist(self):
        settings.SHARED_SERVER = "127.0.0.1"
        instance = Instance(
            name="caravan",
            ec2_id="i-89",
        )
        create_database(instance)
        Instance.objects.filter(name=instance.name)[0].delete()
        try:
            with self.assertRaises(InstanceAlreadyExists):
                create_database(instance)
        finally:
            self.cursor.execute("DROP DATABASE IF EXISTS caravan")

    def test_create_database_invalid_name(self):
        instance = Instance(name="mysql")
        with self.assertRaises(InvalidInstanceName):
            create_database(instance)
