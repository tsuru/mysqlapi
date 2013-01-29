# Copyright 2013 mysqlapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from django.conf import settings


def connect():
    from boto.s3.connection import S3Connection

    return S3Connection(
        settings.S3_ACCESS_KEY,
        settings.S3_SECRET_KEY
    )


def bucket():
    conn = connect()
    return conn.get_bucket(settings.S3_BUCKET)


def last_key():
    key = bucket().get_key("lastkey")
    return key.get_contents_as_string()


def store_data(data):
    from boto.s3.key import Key
    from uuid import uuid4

    key = Key(bucket(), uuid4().hex)
    key.set_contents_from_string(data)

    last_key = Key(bucket(), "lastkey")
    last_key.set_contents_from_string(key.name)
    return key


def get_data():
    key = bucket().get_key(last_key())
    return key.get_contents_as_string()
