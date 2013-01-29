# -*- coding: utf-8 -*-

# Copyright 2013 mysqlapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from django.core.management.base import NoArgsCommand


class Command(NoArgsCommand):

    can_import_settings = True

    def handle_noargs(self, **options):
        return u"Successfully restored!"
