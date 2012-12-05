from unittest import TestCase
from django.conf import settings
from django.test.utils import override_settings

from mysqlapi.api.management.commands import s3

import mock


class S3TestCase(TestCase):
    @override_settings(S3_ACCESS_KEY="access", S3_SECRET_KEY="secret")
    def test_connection_should_get_keys_from_settings(self):
        access = settings.S3_ACCESS_KEY
        secret = settings.S3_SECRET_KEY
        with mock.patch("boto.s3.connection.S3Connection") as s3con:
            s3.connect()
            s3con.assert_called_with(access, secret)
