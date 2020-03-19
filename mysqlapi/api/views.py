# -*- coding: utf-8 -*-

# Copyright 2014 mysqlapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import subprocess

from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.generic.base import View

import crane_ec2

from mysqlapi.api.decorators import basic_auth_required
from mysqlapi.api.models import (create_database, DatabaseManager,
                                 ProvisionedInstance, Instance,
                                 canonicalize_db_name)


class BindApp(View):

    def post(self, request, name, *args, **kwargs):
        name = canonicalize_db_name(name)
        try:
            instance = Instance.objects.get(name=name)
        except Instance.DoesNotExist:
            return HttpResponse("Instance not found", status=404)
        if instance.state != "running":
            msg = u"You can't bind to this instance because it's not running."
            return HttpResponse(msg, status=412)
        db = instance.db_manager()
        try:
            username, password = db.create_user(name, None)
        except Exception as e:
            return HttpResponse(e.args[-1], status=500)
        config = {
            "MYSQL_HOST": db.public_host,
            "MYSQL_PORT": u"3306",
            "MYSQL_DATABASE_NAME": instance.name,
            "MYSQL_USER": username,
            "MYSQL_PASSWORD": password,
        }
        return HttpResponse(json.dumps(config), status=201)

    def delete(self, request, name, *args, **kwargs):
        name = canonicalize_db_name(name)
        try:
            instance = Instance.objects.get(name=name)
        except Instance.DoesNotExist:
            return HttpResponse("Instance not found.", status=404)
        db = instance.db_manager()
        try:
            db.drop_user(name, None)
        except Exception as e:
            return HttpResponse(e.args[-1], status=500)
        return HttpResponse("", status=200)


class BindUnit(View):

    def post(self, request, name, *args, **kwargs):
        return HttpResponse("", status=201)

    def delete(self, request, name, *args, **kwargs):
        return HttpResponse("", status=200)


class CreateDatabase(View):

    def __init__(self, *args, **kwargs):
        super(CreateDatabase, self).__init__(*args, **kwargs)
        self._client = crane_ec2.Client()

    def post(self, request):
        if "name" not in request.POST:
            return HttpResponse("Instance name is missing", status=500)
        name = request.POST.get("name")
        if not name:
            return HttpResponse("Instance name is empty", status=500)
        instance = Instance(name=canonicalize_db_name(name))
        try:
            create_database(instance, self._client)
        except Exception as e:
            return HttpResponse(e.args[-1], status=500)
        return HttpResponse("", status=201)


class DropDatabase(View):

    def __init__(self, *args, **kwargs):
        super(DropDatabase, self).__init__(*args, **kwargs)
        self._client = crane_ec2.Client()

    def delete(self, request, name, *args, **kwargs):
        name = canonicalize_db_name(name)
        try:
            instance = Instance.objects.get(name=name)
        except Instance.DoesNotExist:
            msg = "Can't drop database '%s'; database doesn't exist" % name
            return HttpResponse(msg, status=404)
        if instance.shared:
            db = instance.db_manager()
            db.drop_database()
        elif instance.ec2_id is None:
            pi = ProvisionedInstance.objects.get(instance=instance)
            pi.dealloc()
        elif self._client.unauthorize(instance) and \
                self._client.terminate(instance):
            pass
        else:
            return HttpResponse("Failed to terminate the instance.",
                                status=500)
        instance.delete()
        return HttpResponse("", status=200)


@basic_auth_required
@require_http_methods(["GET"])
def export(request, name):
    host = request.GET.get("service_host", "localhost")
    try:
        db = DatabaseManager(name, host)
        return HttpResponse(db.export())
    except subprocess.CalledProcessError as e:
        return HttpResponse(e.output.split(":")[-1].strip(), status=500)


class Healthcheck(View):

    def __init__(self, *args, **kwargs):
        self._client = crane_ec2.Client()

    def get(self, request, name, *args, **kwargs):
        try:
            instance = Instance.objects.get(name=name)
        except Instance.DoesNotExist:
            return HttpResponse("Instance %s not found" % name, status=404)

        if instance.state == "pending":
            return HttpResponse("pending", status=202)

        # if it is up, we check again to see if the state still the same
        status = 500
        if instance.is_up():
            status = 204

        return HttpResponse(status=status)
