# -*- coding: utf-8 -*-
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
