import unittest

from boto.ec2.regioninfo import RegionInfo
from django.conf import settings
from mocker import Mocker

from mysqlapi import ec2
from mysqlapi.api.models import Instance
from mysqlapi.ec2.tests import mocks


class EC2ClientTestCase(unittest.TestCase):

    def test_ec2_conn_connects_to_ec2_using_data_from_settings_when_not_connected(self):
        fake = mocks.FakeEC2Conn()
        mocker = Mocker()
        r = RegionInfo()
        regioninfo = mocker.replace("boto.ec2.regioninfo.RegionInfo")
        regioninfo(endpoint=settings.EC2_ENDPOINT)
        mocker.result(r)
        connect_ec2 = mocker.replace("boto.connect_ec2")
        connect_ec2(
            aws_access_key_id=settings.EC2_ACCESS_KEY,
            aws_secret_access_key=settings.EC2_SECRET_KEY,
            region=r,
            is_secure=False,
            port=settings.EC2_PORT,
            path=settings.EC2_PATH,
        )
        mocker.result(fake)
        mocker.replay()
        client = ec2.Client()
        conn = client.ec2_conn
        self.assertIsInstance(conn, mocks.FakeEC2Conn)
        mocker.verify()

    def test_run_creates_instance_with_data_from_settings_and_save_it_in_the_database(self):
        instance = Instance(name="professor_xavier")
        client = ec2.Client()
        client._ec2_conn = mocks.FakeEC2Conn()
        ran = client.run(instance)
        self.assertTrue(ran)
        instance = Instance.objects.get(ec2_id="i-00000302", name="professor_xavier")
        self.assertIsNotNone(instance.pk)

    def test_run_returns_False_and_does_not_save_the_instance_in_the_database_if_it_fails_to_boot(self):
        instance = Instance(name="far_cry")
        client = ec2.Client()
        client._ec2_conn = mocks.FailingEC2Conn()
        ran = client.run(instance)
        self.assertFalse(ran)

    def test_get_instance_should_set_instance_state_and_ip_when_its_ready_and_return_True_if_its_ok(self):
        instance = Instance.objects.create(name="good_news_first", ec2_id="i-00000302")
        client = ec2.Client()
        client._ec2_conn = mocks.FakeEC2Conn(times_to_fail=0)
        changed = client.get(instance)
        self.assertTrue(changed)
        other_instance = Instance.objects.get(name="good_news_first")
        self.assertEqual("running", other_instance.state)
        self.assertEqual("10.10.10.10", other_instance.host)

    def test_get_instance_should_return_false_if_instance_is_not_running_or_does_not_have_public_ip_yet(self):
        instance = Instance.objects.create(name="good_news_first", ec2_id="i-00000302")
        try:
            client = ec2.Client()
            client._ec2_conn = mocks.FakeEC2Conn(times_to_fail=1)
            changed = client.get(instance)
            self.assertFalse(changed)
        finally:
            instance.delete()
