from django.http import HttpResponse
from mysqlapi.api.models import DatabaseManager
from django.views.decorators.http import require_http_methods


@require_http_methods(["POST"])
def create(request):
    db = DatabaseManager()
    db.create(request.POST["appname"])
    db.create_user(request.POST["appname"], "localhost")
    return HttpResponse("", status=201)


@require_http_methods(["DELETE"])
def drop(request, appname):
    db = DatabaseManager()
    db.drop(appname)
    db.drop_user(appname, "localhost")
    return HttpResponse("", status=200)
