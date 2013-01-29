# Copyright 2013 mysqlapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase

from mysqlapi.api.management.commands.restore import Command


class RestoreCommandTestCase(TestCase):
    def test_restore(self):
        Command().handle_noargs()
