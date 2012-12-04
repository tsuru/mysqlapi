from unittest import TestCase

from mysqlapi.api.management.commands.export import Command

import mock
import subprocess


class ExportCommandTestCase(TestCase):
    def test_export(self):
        with mock.patch("subprocess.check_output") as check_output:
            Command().handle_noargs()
            check_output.assert_called_with(["mysqldump", "-u", "root", "--quick", "--all-databases", "--compact"], stderr=subprocess.STDOUT)
