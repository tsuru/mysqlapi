from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import simplejson

from mysqlapi.api.models import DatabaseManager


@csrf_exempt
@require_http_methods(["POST"])
def create(request):
    db = DatabaseManager(request.POST["appname"])
    db.create()
    db.create_user()
    config = {
        "MYSQL_DATABASE_NAME": db.name,
        "MYSQL_USER": db.name,
        "MYSQL_PASSWORD": db.password,
        "MYSQL_HOST": db.host,
        "MYSQL_PORT": db.port,
    }
    return HttpResponse(simplejson.dumps(config), status=201)


@csrf_exempt
@require_http_methods(["DELETE"])
def drop(request, appname):
    db = DatabaseManager(appname)
    db.drop()
    db.drop_user()
    return HttpResponse("", status=200)
