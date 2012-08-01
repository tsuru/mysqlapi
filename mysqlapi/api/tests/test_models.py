from django.db.models import CharField
from django.test import TestCase

from mysqlapi.api.models import Instance


class InstanceTestCase(TestCase):

    def test_instance_should_have_a_name(self):
        self.assertIn("name", Instance._meta.get_all_field_names())

    def test_instance_name_should_be_CharField(self):
        field = Instance._meta.get_field_by_name("name")[0]
        self.assertIsInstance(field, CharField)

    def test_instance_name_should_have_at_most_100_characters(self):
        field = Instance._meta.get_field_by_name("name")[0]
        self.assertEqual(100, field.max_length)

    def test_instance_should_have_an_ec2_id(self):
        self.assertIn("ec2_id", Instance._meta.get_all_field_names())

    def test_ec2_id_should_be_CharField(self):
        field = Instance._meta.get_field_by_name("ec2_id")[0]
        self.assertIsInstance(field, CharField)

    def test_ec2_id_should_have_at_most_100_characters(self):
        field = Instance._meta.get_field_by_name("ec2_id")[0]
        self.assertEqual(100, field.max_length)

    def test_instance_should_have_an_state(self):
        self.assertIn("state", Instance._meta.get_all_field_names())

    def test_state_should_be_CharField(self):
        field = Instance._meta.get_field_by_name("state")[0]
        self.assertIsInstance(field, CharField)

    def test_state_should_have_at_most_50_characters(self):
        field = Instance._meta.get_field_by_name("state")[0]
        self.assertEqual(50, field.max_length)

    def test_state_should_be_pending_by_default(self):
        field = Instance._meta.get_field_by_name("state")[0]
        self.assertEqual("pending", field.default)

    def test_state_should_have_choices(self):
        expected = (
            ("pending", "pending"),
            ("running", "running"),
            ("error", "error"),
        )
        field = Instance._meta.get_field_by_name("state")[0]
        self.assertEqual(expected, field.choices)

    def test_instance_should_have_a_host(self):
        self.assertIn("host", Instance._meta.get_all_field_names())

    def test_host_should_be_CharField(self):
        field = Instance._meta.get_field_by_name("host")[0]
        self.assertIsInstance(field, CharField)

    def test_host_should_have_at_most_50_characters(self):
        field = Instance._meta.get_field_by_name("host")[0]
        self.assertEqual(50, field.max_length)

    def test_host_should_accept_empty_values(self):
        field = Instance._meta.get_field_by_name("host")[0]
        self.assertTrue(field.blank)

    def test_host_should_accept_null_values(self):
        field = Instance._meta.get_field_by_name("host")[0]
        self.assertTrue(field.null)

    def test_instance_should_have_reason_of_failure(self):
        self.assertIn("reason", Instance._meta.get_all_field_names())

    def test_reason_should_be_CharField(self):
        field = Instance._meta.get_field_by_name("reason")[0]
        self.assertIsInstance(field, CharField)

    def test_reason_should_have_at_most_1000_characters(self):
        field = Instance._meta.get_field_by_name("reason")[0]
        self.assertEqual(1000, field.max_length)

    def test_reason_should_accept_null_values(self):
        field = Instance._meta.get_field_by_name("reason")[0]
        self.assertTrue(field.null)

    def test_reason_should_accept_blank(self):
        field = Instance._meta.get_field_by_name("reason")[0]
        self.assertTrue(field.blank)

    def test_reason_should_have_None_as_default_value(self):
        field = Instance._meta.get_field_by_name("reason")[0]
        self.assertEqual(None, field.default)
