# -*- coding: utf-8 -*-
from django.core.management.base import NoArgsCommand

from mysqlapi.api.database import export


class Command(NoArgsCommand):

    can_import_settings = True

    def handle_noargs(self, **options):
        export()
        return u"Successfully exported!"
