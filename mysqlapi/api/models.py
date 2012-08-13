import hashlib
import os
import subprocess
import threading
import time
import uuid

from django.conf import settings
from django.db import models

from mysqlapi.api.database import Connection


def generate_password():
    return hashlib.sha1(uuid.uuid4().hex).hexdigest()


def generate_user(username):
    if len(username) > 16:
        _username = username[:12] + generate_password()[:4]
    else:
        _username = username
    return _username


class DatabaseCreationException(BaseException):
    pass


class DatabaseManager(object):

    def __init__(self, name, host="localhost", user="root", password=""):
        self.name = name
        self._host = host
        self.port = '3306'
        self.conn = Connection(self._host, user, password, "")

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

    def is_up(self, manager):
        if self.state == "running" and manager.is_up():
            return True
        return False


class DatabaseCreator(threading.Thread):

    def __init__(self, ec2_client, instance, user="root", password=""):
        self.instance = instance
        self.ec2_client = ec2_client
        self.user = user
        self.password = password
        super(DatabaseCreator, self).__init__()

    def _error(self, exc):
        self.ec2_client.unauthorize(self.instance)
        self.ec2_client.terminate(self.instance)
        self.instance.state = "error"
        self.instance.reason = unicode(exc)
        self.instance.save()

    def run(self):
        while not self.ec2_client.get(self.instance):
            time.sleep(settings.EC2_POLL_INTERVAL)
        if not self.ec2_client.authorize(self.instance):
            self._error("Failed to authorize access to the instance.")
            return
        try:
            db = DatabaseManager(self.instance.name, host=self.instance.host, user=self.user, password=self.password)
            db.create_database()
            self.instance.save()
        except Exception as exc:
            self._error(exc)


def create_database(instance, ec2_client=None):
    if not ec2_client.run(instance):
        raise DatabaseCreationException(instance, "Failed to create EC2 instance.")
    instance.save()
    t = DatabaseCreator(ec2_client, instance)
    t.start()
    return t
