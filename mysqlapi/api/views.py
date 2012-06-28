from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import simplejson
from django.conf import settings
from django.db import DatabaseError

from mysqlapi.api.models import DatabaseManager

import subprocess


@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def create_user_or_drop_database(request, name):
    if request.method == "POST":
        return create_user(request, name)
    if request.method == "DELETE":
        return drop_database(request, name)


@csrf_exempt
@require_http_methods(["POST"])
def create_user(request, name):
    if not "hostname" in request.POST:
        return HttpResponse("Hostname is missing", status=500)
    hostname = request.POST.get("hostname", None)
    if not hostname:
        return HttpResponse("Hostname is empty", status=500)
    db = DatabaseManager(name, host=hostname)
    try:
        db.create_user()
    except DatabaseError, e:
        return HttpResponse(e[1], status=500)
    config = {
        "MYSQL_USER": db.username,
        "MYSQL_PASSWORD": db.password,
    }
    return HttpResponse(simplejson.dumps(config), status=201)


@csrf_exempt
@require_http_methods(["POST"])
def create_database(request):
    if not "name" in request.POST:
        return HttpResponse("App name is missing", status=500)
    name = request.POST.get("name", None)
    if not name:
        return HttpResponse("App name is empty", status=500)
    db = DatabaseManager(name)
    try:
        db.create()
    except DatabaseError, e:
        return HttpResponse(e[1], status=500)
    config = {
        "MYSQL_DATABASE_NAME": db.name,
        "MYSQL_HOST": settings.DATABASES["default"]["HOST"],
        "MYSQL_PORT": db.port,
    }
    return HttpResponse(simplejson.dumps(config), status=201)


@csrf_exempt
@require_http_methods(["DELETE"])
def drop_user(request, name, hostname):
    db = DatabaseManager(name, host=hostname)
    try:
        db.drop_user()
    except DatabaseError, e:
        return HttpResponse(e[1], status=500)
    return HttpResponse("", status=200)


@csrf_exempt
@require_http_methods(["DELETE"])
def drop_database(request, name):
    db = DatabaseManager(name)
    try:
        db.drop()
    except DatabaseError, e:
        return HttpResponse(e[1], status=500)
    return HttpResponse("", status=200)


@require_http_methods(["GET"])
def export(request, name):
    try:
        db = DatabaseManager(name)
        return HttpResponse(db.export())
    except subprocess.CalledProcessError, e:
        return HttpResponse(e.output.split(":")[-1].strip(), status=500)
