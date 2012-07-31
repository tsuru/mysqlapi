from django.test import TestCase

from mysqlapi.api.views import _get_service_host


class GetServiceHostTestCase(TestCase):

    def test_get_service_host_returns_localhost_if_the_key_is_not_present(self):
        self.assertEqual("localhost", _get_service_host({}))

    def test_get_service_host_returns_the_value_of_service_host_key_if_present(self):
        self.assertEqual("service.net", _get_service_host({"service_host": "service.net"}))

    def test_get_service_host_returns_localhost_if_the_key_is_an_empty_string(self):
        self.assertEqual("localhost", _get_service_host({"service_host": ""}))
