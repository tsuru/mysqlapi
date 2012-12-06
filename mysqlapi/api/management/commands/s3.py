from django.conf import settings


def connect():
    from boto.s3.connection import S3Connection

    return S3Connection(
        settings.S3_ACCESS_KEY,
        settings.S3_SECRET_KEY
    )


def bucket():
    conn = connect()
    return conn.create_bucket(settings.S3_BUCKET)


def last_key():
    key = bucket().get_key("lastkey")
    return key.get_contents_as_string()
