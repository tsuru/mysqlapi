# -*- coding: utf-8 -*-
import subprocess

import boto
from boto.ec2.regioninfo import RegionInfo

from django.conf import settings
from django.http import HttpResponse
from django.utils import simplejson
from django.views.decorators.http import require_http_methods
from django.views.generic.base import View

from mysqlapi.api.models import DatabaseManager


def _get_service_host(dict):
    host = dict.get("service_host")
    if not host:
        host = "localhost"
    return host


@require_http_methods(["POST", "DELETE"])
def create_user_or_drop_database(request, name):
    if request.method == "POST":
        return create_user(request, name)
    if request.method == "DELETE":
        return drop_database(request, name)


@require_http_methods(["POST"])
def create_user(request, name):
    if not "hostname" in request.POST:
        return HttpResponse("Hostname is missing", status=500)
    hostname = request.POST.get("hostname", None)
    if not hostname:
        return HttpResponse("Hostname is empty", status=500)
    host = _get_service_host(request.POST)
    db = DatabaseManager(name, host)
    try:
        username, password = db.create_user(name, hostname)
    except Exception, e:
        return HttpResponse(e[1], status=500)
    config = {
        "MYSQL_USER": username,
        "MYSQL_PASSWORD": password,
    }
    return HttpResponse(simplejson.dumps(config), status=201)


class CreateDatabase(View):

    def __init__(self, *args, **kwargs):
        super(CreateDatabase, self).__init__(*args, **kwargs)
        self._ec2_conn = None

    @property
    def ec2_conn(self):
        if not self._ec2_conn:
            self._ec2_conn = boto.connect_ec2(
                aws_access_key_id=settings.EC2_ACCESS_KEY,
                aws_secret_access_key=settings.EC2_SECRET_KEY,
                region=RegionInfo(endpoint=settings.EC2_ENDPOINT),
                is_secure=False,
                port=settings.EC2_PORT,
                path=settings.EC2_PATH,
            )
        return self._ec2_conn

    def post(self, request):
        if not "name" in request.POST:
            return HttpResponse("App name is missing", status=500)
        name = request.POST.get("name", None)
        if not name:
            return HttpResponse("App name is empty", status=500)
        host = _get_service_host(request.POST)
        db = DatabaseManager(name, host)
        try:
            db.create_database()
            self.ec2_conn.run_instances(
                settings.EC2_AMI,
                key_name=settings.EC2_KEY_NAME,
                security_groups=["default"],
            )
        except Exception, e:
            return HttpResponse(e[1], status=500)
        config = {
            "MYSQL_DATABASE_NAME": db.name,
            "MYSQL_HOST": db.host,
            "MYSQL_PORT": db.port,
        }
        return HttpResponse(simplejson.dumps(config), status=201)


@require_http_methods(["DELETE"])
def drop_user(request, name, hostname):
    host = _get_service_host(request.GET)
    db = DatabaseManager(name, host)
    try:
        db.drop_user(name, hostname)
    except Exception, e:
        return HttpResponse(e[1], status=500)
    return HttpResponse("", status=200)


@require_http_methods(["DELETE"])
def drop_database(request, name):
    host = _get_service_host(request.GET)
    db = DatabaseManager(name, host)
    try:
        db.drop_database()
    except Exception, e:
        return HttpResponse(e[1], status=500)
    return HttpResponse("", status=200)


@require_http_methods(["GET"])
def export(request, name):
    host = request.GET.get("service_host", "localhost")
    try:
        db = DatabaseManager(name, host)
        return HttpResponse(db.export())
    except subprocess.CalledProcessError, e:
        return HttpResponse(e.output.split(":")[-1].strip(), status=500)


@require_http_methods(["GET"])
def healthcheck(request, name):
    host = _get_service_host(request.GET)
    db = DatabaseManager(name, host)
    status = db.is_up() and 204 or 500
    return HttpResponse(status=status)
