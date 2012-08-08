# -*- coding: utf-8 -*-
import subprocess

from django.http import HttpResponse
from django.utils import simplejson
from django.views.decorators.http import require_http_methods
from django.views.generic.base import View

import crane_ec2
from mysqlapi.api.models import create_database, DatabaseManager, Instance


def _get_service_host(dict):
    host = dict.get("service_host")
    if not host:
        host = "localhost"
    return host


class CreateUser(View):

    def post(self, request, name, *args, **kwargs):
        if not "hostname" in request.POST:
            return HttpResponse("Hostname is missing", status=500)
        hostname = request.POST.get("hostname", None)
        if not hostname:
            return HttpResponse("Hostname is empty", status=500)
        try:
            instance = Instance.objects.get(name=name)
        except Instance.DoesNotExist:
            return HttpResponse("Instance not found", status=404)
        if instance.state != "running":
            return HttpResponse(u"You can't bind to this instance because it's not running.", status=412)
        db = DatabaseManager(name, instance.host)
        try:
            username, password = db.create_user(name, hostname)
        except Exception, e:
            return HttpResponse(e.args[-1], status=500)
        config = {
            "MYSQL_USER": username,
            "MYSQL_PASSWORD": password,
        }
        return HttpResponse(simplejson.dumps(config), status=201)


class CreateDatabase(View):

    def __init__(self, *args, **kwargs):
        super(CreateDatabase, self).__init__(*args, **kwargs)
        self._client = crane_ec2.Client()

    def post(self, request):
        if not "name" in request.POST:
            return HttpResponse("App name is missing", status=500)
        name = request.POST.get("name")
        if not name:
            return HttpResponse("App name is empty", status=500)
        instance = Instance(name=name)
        try:
            create_database(instance, self._client)
        except Exception, e:
            return HttpResponse(e.args[-1], status=500)
        return HttpResponse("ok", status=201)


@require_http_methods(["DELETE"])
def drop_user(request, name, hostname):
    host = _get_service_host(request.GET)
    db = DatabaseManager(name, host)
    try:
        db.drop_user(name, hostname)
    except Exception, e:
        return HttpResponse(e.args[-1], status=500)
    return HttpResponse("", status=200)


class CreateUserOrDropDatabase(View):

    def post(self, request, name, *args, **kwargs):
        return CreateUser.as_view()(request, name)

    def delete(self, request, name, *args, **kwargs):
        return DropDatabase.as_view()(request, name)


class DropDatabase(View):

    def __init__(self, *args, **kwargs):
        super(DropDatabase, self).__init__(*args, **kwargs)
        self._client = crane_ec2.Client()

    def delete(self, request, name, *args, **kwargs):
        try:
            instance = Instance.objects.get(name=name)
        except Instance.DoesNotExist:
            return HttpResponse("Can't drop database 'doesnotexists'; database doesn't exist", status=500)
        self._client.terminate(instance)
        instance.delete()
        host = _get_service_host(request.GET)
        db = DatabaseManager(name, host)
        try:
            db.drop_database()
        except Exception, e:
            return HttpResponse(e.args[-1], status=500)
        return HttpResponse("", status=200)


@require_http_methods(["GET"])
def export(request, name):
    host = request.GET.get("service_host", "localhost")
    try:
        db = DatabaseManager(name, host)
        return HttpResponse(db.export())
    except subprocess.CalledProcessError, e:
        return HttpResponse(e.output.split(":")[-1].strip(), status=500)


class Healthcheck(View):

    def __init__(self, *args, **kwargs):
        self._client = crane_ec2.Client()

    def get(self, request, name, *args, **kwargs):
        try:
            instance = Instance.objects.get(name=name)
        except Instance.DoesNotExist:
            return HttpResponse("Instance %s not found" % name, status=404)

        host = _get_service_host(request.GET)
        db = DatabaseManager(name, host)

        # if the vm is not up and running, there's no need to check it again
        # just let the responsible thread to update it
        if not instance.is_up(db):
            return HttpResponse(status=500)

        # if it is up, we check again to see if the state still the same
        self._client.get(instance)
        status = 500
        if instance.is_up(db):
            status = 204

        return HttpResponse(status=status)
