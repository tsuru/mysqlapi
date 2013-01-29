# -*- coding: utf-8 -*-

# Copyright 2013 mysqlapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import traceback

from django.test import TestCase

from mysqlapi.api.database import Connection


class DatabaseConnectionTestCase(TestCase):

    def test_connection_should_return_a_connection(self):
        conn = Connection(hostname="localhost", username="root")
        conn.open()
        self.assertTrue(conn._connection)
        conn.close()

    def test_should_return_cursor(self):
        conn = Connection(hostname="localhost", username="root")
        conn.open()
        self.assertTrue(conn.cursor())
        conn.close()

    def test_close_does_not_fail_when_connection_is_None(self):
        conn = Connection(hostname="localhost", username="root")
        try:
            conn.close()
        except Exception as e:
            msg = "Should not raise any exception when closing a None " +\
                  "connection, but raised:\n%s"
            self.fail(msg % traceback.format_exc(e))
