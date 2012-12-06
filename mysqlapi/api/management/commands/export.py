# -*- coding: utf-8 -*-
from django.core.management.base import NoArgsCommand

from mysqlapi.api.database import export
from mysqlapi.api.management.commands import s3


class Command(NoArgsCommand):

    can_import_settings = True

    def handle_noargs(self, **options):
        data = export()
        self.send_data(data)
        return u"Successfully exported!"

    def send_data(self, data):
        s3.store_data(data)
