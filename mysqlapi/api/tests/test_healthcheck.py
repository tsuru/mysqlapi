from django.test import TestCase
from django.test.client import RequestFactory
from mocker import Mocker

from mysqlapi.api.models import Instance
from mysqlapi.api.tests import mocks
from mysqlapi.api.views import Healthcheck


class HealthcheckTestCase(TestCase):

    def setUp(self):
        self.instance = Instance.objects.create(name="g8mysql")

    def tearDown(self):
        self.instance.delete()

    def test_healthcheck_returns_204_if_the_mysql_server_is_on(self):
        mocker = Mocker()
        obj = mocker.replace("mysqlapi.api.models.DatabaseManager.is_up")
        obj()
        mocker.result(True)
        mocker.replay()
        request = RequestFactory().get("/resources/g8mysql/status/")
        view = Healthcheck()
        fake = mocks.FakeEC2Client()
        view._client = fake
        response = view.get(request, "g8mysql")
        self.assertEqual(204, response.status_code)
        mocker.verify()

    def test_healthcheck_returns_500_if_the_mysql_server_is_off(self):
        mocker = Mocker()
        obj = mocker.replace("mysqlapi.api.models.DatabaseManager.is_up")
        obj()
        mocker.result(False)
        mocker.replay()
        request = RequestFactory().get("/resources/g8mysql/status/")
        view = Healthcheck()
        fake = mocks.FakeEC2Client()
        view._client = fake
        response = view.get(request, "g8mysql")
        self.assertEqual(500, response.status_code)
        mocker.verify()

    def test_healthcheck_calls_ec2_get_when_instance_is_running_and_returns_201(self):
        mocker = Mocker()
        obj = mocker.replace("mysqlapi.api.models.DatabaseManager.is_up")
        obj()
        mocker.result(True)
        mocker.replay()

        request = RequestFactory().get("/resources/g8mysql/status/")
        view = Healthcheck()
        fake = mocks.FakeEC2Client()
        view._client = fake

        response = view.get(request, "g8mysql")
        self.assertEqual(204, response.status_code)
        self.assertEqual(["get instance g8mysql"], fake.actions)
        mocker.verify()

    def test_healthcheck_calls_ec2_get_when_instance_is_pending_and_returns_500(self):
        request = RequestFactory().get("/resources/g8mysql/status/")
        view = Healthcheck()
        fake = mocks.FakeEC2ClientPendingInstance()
        view._client = fake

        response = view.get(request, "g8mysql")
        self.assertEqual(500, response.status_code)
        self.assertEqual(["get instance g8mysql"], fake.actions)
