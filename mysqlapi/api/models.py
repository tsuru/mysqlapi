# Copyright 2013 mysqlapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import hashlib
import os
import re
import subprocess

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


class DatabaseCreationError(Exception):
    pass


def generate_password():
    return hashlib.sha1(str(os.urandom(256)).encode('utf-8')).hexdigest()


def generate_user(username, host):
    userhost = username + '-' + host
    if len(userhost) > 20:
        _userhost = userhost[:20]
    else:
        _userhost = userhost
    return (_userhost + '-' + hashlib.sha1(str(username + host).encode('utf-8')).hexdigest())[:32]


class DatabaseManager(object):

    def __init__(self,
                 name,
                 host="localhost",
                 port="3306",
                 user="root",
                 password="",
                 public_host=None):
        self.name = canonicalize_db_name(name)
        self._host = host
        self.port = port
        self.conn = Connection(self._host, self.port, user, password, "")
        self._public_host = public_host

    @property
    def public_host(self):
        if self._public_host:
            return self._public_host
        return self.host

    def create_database(self):
        self.conn.open()
        cursor = self.conn.cursor()
        if settings.MSQL_5_VERSION_ENABLED:
            sql = "CREATE DATABASE %s default character set utf8 " + \
                  "default collate utf8_general_ci"
        else:
            sql = "CREATE DATABASE %s default character set utf8mb4 " + \
                  "default collate utf8mb4_unicode_ci"
        cursor.execute(sql % self.name)
        self.conn.close()

    def drop_database(self):
        self.conn.open()
        cursor = self.conn.cursor()
        cursor.execute("DROP DATABASE %s" % self.name)
        self.conn.close()

    def create_user(self, username, host):
        self.conn.open()
        cursor = self.conn.cursor()
        username = generate_user(username, host)
        password = generate_password()

        if settings.MSQL_5_VERSION_ENABLED:
            sql = ("grant all privileges on {0}.* to '{1}'@'%'"
                   " identified by '{2}'")
            cursor.execute(sql.format(self.name, username, password))
        else:
            sql = ("CREATE USER '{0}'@'%' IDENTIFIED BY '{1}';")
            cursor.execute(sql.format(username, password))
            sql = ("GRANT ALL PRIVILEGES ON {0}.* TO '{1}'@'%';")
            cursor.execute(sql.format(self.name, username))
        self.conn.close()
        return username, password

    def drop_user(self, username, host):
        self.conn.open()
        cursor = self.conn.cursor()
        username = generate_user(username, host)
        cursor.execute("drop user '{0}'@'%'".format(username))
        self.conn.close()

    def export(self):
        cmd = ["mysqldump", "-u", "root", "-d", self.name, "--compact"]
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT)

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
    state = models.CharField(max_length=50,
                             default="pending",
                             choices=STATE_CHOICES)
    reason = models.CharField(max_length=1000,
                              null=True,
                              blank=True,
                              default=None)
    host = models.CharField(max_length=50, null=True, blank=True)
    port = models.CharField(max_length=5, default="3306")
    shared = models.BooleanField(default=False)

    def is_up(self):
        return self.state == "running" and self.db_manager().is_up()

    def db_manager(self):
        host = self.host
        port = self.port
        user = "root"
        password = ""
        public_host = None
        if self.shared:
            host = settings.SHARED_SERVER
            user = settings.SHARED_USER
            password = settings.SHARED_PASSWORD
            public_host = settings.SHARED_SERVER_PUBLIC_HOST
        elif ProvisionedInstance.objects.filter(instance=self).exists():
            pi = ProvisionedInstance.objects.get(instance=self)
            user = pi.admin_user
            password = pi.admin_password
        return DatabaseManager(self.name,
                               host=host,
                               port=port,
                               user=user,
                               password=password,
                               public_host=public_host)


class ProvisionedInstance(models.Model):
    instance = models.OneToOneField(Instance, null=True, blank=True, on_delete = models.CASCADE)
    host = models.CharField(max_length=500)
    port = models.IntegerField(default=3306)
    admin_user = models.CharField(max_length=255, default="root")
    admin_password = models.CharField(max_length=255, blank=True)

    def _manager(self, name=None):
        if not hasattr(self, "_db_manager"):
            self._db_manager = DatabaseManager(name=self.instance.name,
                                               host=self.host,
                                               port=self.port,
                                               user=self.admin_user,
                                               password=self.admin_password)
        return self._db_manager

    def alloc(self, instance):
        if self.instance:
            raise TypeError("This instance is not available")
        self.instance = instance
        try:
            self._manager().create_database()
        except Exception as exc:
            raise DatabaseCreationError(*exc.args)
        instance.host = self.host
        instance.port = str(self.port)
        instance.shared = False
        instance.ec2_id = None
        instance.state = "running"
        instance.save()
        self.instance = instance
        self.save()

    def dealloc(self):
        if not self.instance:
            raise TypeError("This instance is not allocated")
        self._manager().drop_database()
        self.instance.state = "stopped"
        self.instance = None
        self.save()


def create_database(instance, ec2_client=None):
    instance.name = canonicalize_db_name(instance.name)
    if instance.name in settings.RESERVED_NAMES:
        raise InvalidInstanceName(name=instance.name)
    if Instance.objects.filter(name=instance.name):
        raise InstanceAlreadyExists(name=instance.name)
    if settings.SHARED_SERVER:
        return _create_shared_database(instance)
    elif settings.USE_POOL:
        return _create_from_pool(instance)
    else:
        return _create_dedicate_database(instance, ec2_client)


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


def _create_from_pool(instance):
    provisioned_instance = ProvisionedInstance.objects.filter(
        instance__isnull=True)[:1]
    if not provisioned_instance:
        raise DatabaseCreationError(instance,
                                    "No free instances available in the pool")
    provisioned_instance[0].alloc(instance)


def _create_dedicate_database(instance, ec2_client):
    if not ec2_client.run(instance):
        raise DatabaseCreationError(instance,
                                    "Failed to create EC2 instance.")
    instance.save()
    creator.enqueue(instance)


def canonicalize_db_name(name):
    if re.search(r"[\W\s]", name) is not None:
        prefix = hashlib.sha1(str(name).encode('utf-8')).hexdigest()[:10]
        name = re.sub(r"[\W\s]", "_", name) + prefix
    return name
