# -*- coding: utf-8 -*-

# Copyright 2013 mysqlapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from unittest import TestCase

from mysqlapi.api.database import export

import mock
import subprocess


class ExportTestCase(TestCase):

    def test_export(self):
        with mock.patch("subprocess.check_output") as check_output:
            export()
            cmd = ["mysqldump", "-u", "root", "--quick",
                   "--all-databases", "--compact"]
            check_output.assert_called_with(cmd, stderr=subprocess.STDOUT)
