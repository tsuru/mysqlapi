from django.test import TestCase
from django.test.client import RequestFactory
from mocker import Mocker

from mysqlapi.api.views import healthcheck


class HealthcheckTestCase(TestCase):

    def test_healthcheck_returns_204_if_the_mysql_server_is_on(self):
        mocker = Mocker()
        obj = mocker.replace("mysqlapi.api.models.DatabaseManager.is_up")
        obj()
        mocker.result(True)
        mocker.replay()
        request = RequestFactory().get("/resources/g8mysql/status/")
        response = healthcheck(request, "g8mysql")
        self.assertEqual(204, response.status_code)
        mocker.verify()

    def test_healthcheck_returns_500_if_the_mysql_server_is_off(self):
        mocker = Mocker()
        obj = mocker.replace("mysqlapi.api.models.DatabaseManager.is_up")
        obj()
        mocker.result(False)
        mocker.replay()
        request = RequestFactory().get("/resources/g8mysql/status/")
        response = healthcheck(request, "g8mysql")
        self.assertEqual(500, response.status_code)
        mocker.verify()
