from django.http import HttpResponse
from mysqlapi.api.models import DatabaseManager


def create(request):
    db = DatabaseManager()
    db.create(request.POST["appname"])
    db.create_user(request.POST["appname"], "localhost")
    return HttpResponse("", status=201)


def drop(request, appname):
    db = DatabaseManager()
    db.drop(appname)
    db.drop_user(appname, "localhost")
    return HttpResponse("", status=200)
