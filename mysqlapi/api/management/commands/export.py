# -*- coding: utf-8 -*-
from django.core.management.base import NoArgsCommand
from django.conf import settings

from mysqlapi.api.database import export


class Command(NoArgsCommand):

    can_import_settings = True

    def handle_noargs(self, **options):
        data = export()
        self.send_data(data)
        return u"Successfully exported!"

    def send_data(self, data):
        from boto.s3.key import Key
        from boto.s3.connection import S3Connection

        conn = S3Connection(
            settings.S3_ACCESS_KEY,
            settings.S3_SECRET_KEY
        )
        bucket = conn.create_bucket(settings.S3_BUCKET)
        key = Key(bucket)
        key.set_contents_from_string(data)
