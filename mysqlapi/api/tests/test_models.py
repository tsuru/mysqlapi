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

    def test_instance_should_have_an_instance_id(self):
        self.assertIn("instance_id", Instance._meta.get_all_field_names())

    def test_instance_id_should_be_CharField(self):
        field = Instance._meta.get_field_by_name("instance_id")[0]
        self.assertIsInstance(field, CharField)

    def test_instance_id_should_have_at_most_100_characters(self):
        field = Instance._meta.get_field_by_name("instance_id")[0]
        self.assertEqual(100, field.max_length)
