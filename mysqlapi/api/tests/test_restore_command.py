from unittest import TestCase

from mysqlapi.api.management.commands.restore import Command


class RestoreCommandTestCase(TestCase):
    def test_restore(self):
        Command().handle_noargs()
