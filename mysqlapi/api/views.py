from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import simplejson
from django.conf import settings

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
    host = request.POST.get("service_host", "localhost")
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


@csrf_exempt
@require_http_methods(["POST"])
def create_database(request):
    if not "name" in request.POST:
        return HttpResponse("App name is missing", status=500)
    name = request.POST.get("name", None)
    if not name:
        return HttpResponse("App name is empty", status=500)
    host = request.POST.get("service_host", "localhost")
    db = DatabaseManager(name, host)
    try:
        db.create_database()
    except Exception, e:
        return HttpResponse(e[1], status=500)
    config = {
        "MYSQL_DATABASE_NAME": db.name,
        "MYSQL_HOST": db.host,
        "MYSQL_PORT": db.port,
    }
    return HttpResponse(simplejson.dumps(config), status=201)


@csrf_exempt
@require_http_methods(["DELETE"])
def drop_user(request, name, hostname):
    db = DatabaseManager(name)
    try:
        db.drop_user(name, hostname)
    except Exception, e:
        return HttpResponse(e[1], status=500)
    return HttpResponse("", status=200)


@csrf_exempt
@require_http_methods(["DELETE"])
def drop_database(request, name):
    db = DatabaseManager(name)
    try:
        db.drop_database()
    except Exception, e:
        return HttpResponse(e[1], status=500)
    return HttpResponse("", status=200)


@require_http_methods(["GET"])
def export(request, name):
    try:
        db = DatabaseManager(name)
        return HttpResponse(db.export())
    except subprocess.CalledProcessError, e:
        return HttpResponse(e.output.split(":")[-1].strip(), status=500)
