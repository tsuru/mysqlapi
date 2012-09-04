import hashlib
import os
import subprocess
import uuid

import MySQLdb

from django.conf import settings
from django.db import models

from mysqlapi.api import creator
from mysqlapi.api.database import Connection


class InvalidInstanceName(Exception):

    def __init__(self, name):
        self.args = [u"%s is a invalid name."]


class InstanceAlreadyExists(Exception):

    def __init__(self, name):
        self.args = [u"Instance %s already exists." % name]


class DatabaseCreationException(BaseException):
    pass


def generate_password():
    return hashlib.sha1(uuid.uuid4().hex).hexdigest()


def generate_user(username):
    if len(username) > 16:
        _username = username[:12] + generate_password()[:4]
    else:
        _username = username
    return _username


class DatabaseManager(object):

    def __init__(self, name, host="localhost", user="root", password="", public_host=None):
        self.name = name
        self._host = host
        self.port = '3306'
        self.conn = Connection(self._host, user, password, "")
        self._public_host = public_host

    @property
    def public_host(self):
        if self._public_host:
            return self._public_host
        return self.host

    def create_database(self):
        self.conn.open()
        cursor = self.conn.cursor()
        cursor.execute("CREATE DATABASE %s default character set utf8 default collate utf8_general_ci" % self.name)
        self.conn.close()

    def drop_database(self):
        self.conn.open()
        cursor = self.conn.cursor()
        cursor.execute("DROP DATABASE %s" % self.name)
        self.conn.close()

    def create_user(self, username, host):
        self.conn.open()
        cursor = self.conn.cursor()
        username = generate_user(username)
        password = generate_password()
        cursor.execute("grant all privileges on %s.* to %s@%s identified by '%s'" % (self.name, username, host, password))
        self.conn.close()
        return username, password

    def drop_user(self, username, host):
        self.conn.open()
        cursor = self.conn.cursor()
        cursor.execute("drop user %s@%s" % (username, host))
        self.conn.close()

    def export(self):
        return subprocess.check_output(["mysqldump", "-u", "root", "-d", self.name, "--compact"], stderr=subprocess.STDOUT)

    def is_up(self):
        try:
            self.conn.open()
            return True
        except:
            return False
        finally:
            self.conn.close()

    @property
    def host(self):
        if self._host == "localhost":
            return os.environ.get("MYSQLAPI_DATABASE_HOST", "localhost")
        return self._host


class Instance(models.Model):
    STATE_CHOICES = (
        ("pending", "pending"),
        ("running", "running"),
        ("error", "error"),
    )

    name = models.CharField(max_length=100, unique=True)
    ec2_id = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=50, default="pending", choices=STATE_CHOICES)
    reason = models.CharField(max_length=1000, null=True, blank=True, default=None)
    host = models.CharField(max_length=50, null=True, blank=True)
    port = models.CharField(max_length=5, default="3306")
    shared = models.BooleanField(default=False)

    def is_up(self):
        if self.state == "running" and self.db_manager().is_up():
            return True
        return False

    def db_manager(self):
        host = self.host
        user = "root"
        password = ""
        public_host = None
        if self.shared:
            host = settings.SHARED_SERVER
            user = settings.SHARED_USER
            password = settings.SHARED_PASSWORD
            public_host = settings.SHARED_SERVER_PUBLIC_HOST
        return DatabaseManager(self.name, host=host, user=user, password=password, public_host=public_host)


def _create_shared_database(instance):
    db = DatabaseManager(
        name=instance.name,
        host=settings.SHARED_SERVER,
        user=settings.SHARED_USER,
        password=settings.SHARED_PASSWORD,
    )
    try:
        db.create_database()
    except MySQLdb.ProgrammingError as e:
        if len(e.args) > 1 and "database exists" in e.args[1]:
            raise InstanceAlreadyExists(name=instance.name)
        raise
    instance.state = "running"
    instance.shared = True
    instance.ec2_id = None
    instance.save()


def _create_dedicate_database(instance, ec2_client):
    if not ec2_client.run(instance):
        raise DatabaseCreationException(instance, "Failed to create EC2 instance.")
    instance.save()
    creator.enqueue(instance)


def create_database(instance, ec2_client=None):
    if instance.name in settings.RESERVED_NAMES:
        raise InvalidInstanceName(name=instance.name)
    if Instance.objects.filter(name=instance.name):
        raise InstanceAlreadyExists(name=instance.name)
    if settings.SHARED_SERVER:
        return _create_shared_database(instance)
    else:
        return _create_dedicate_database(instance, ec2_client)
