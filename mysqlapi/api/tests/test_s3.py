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

    @override_settings(S3_BUCKET="bucket")
    def test_get_buckets_from_settings(self):
        bucket = settings.S3_BUCKET
        with mock.patch("boto.s3.connection.S3Connection") as s3con:
            conn = mock.Mock()
            s3_instance = s3con.return_value
            s3_instance.return_value = conn
            s3.bucket()
            s3_instance.create_bucket.assert_called_with(bucket)

    def test_last_key(self):
        with mock.patch("mysqlapi.api.management.commands.s3.bucket") as bucket_mock:
            key = mock.Mock()
            key.get_contents_as_string.return_value = "last_key"
            bucket = mock.Mock()
            bucket.get_key.return_value = key
            bucket_mock.return_value = bucket
            self.assertEqual("last_key", s3.last_key())

    def test_store_data(self):
        with mock.patch("mysqlapi.api.management.commands.s3.bucket") as bucket:
            with mock.patch("boto.s3.key.Key") as Key:
                key = Key.return_value
                s3.store_data("data")
                key.set_contents_from_string.assert_called_with("data")

    def test_get_data(self):
        with mock.patch("mysqlapi.api.management.commands.s3.bucket") as bucket_mock:
            key = mock.Mock()
            key.get_contents_as_string.return_value = "last_key"
            bucket = mock.Mock()
            bucket.get_key.return_value = key
            bucket_mock.return_value = bucket
            self.assertEqual("last_key", s3.get_data())
