from django.http import HttpResponse
from mysqlapi.api.models import DatabaseManager
from django.views.decorators.http import require_http_methods


@require_http_methods(["POST"])
def create(request):
    db = DatabaseManager(request.POST["appname"])
    db.create()
    db.create_user()
    return HttpResponse("", status=201)


@require_http_methods(["DELETE"])
def drop(request, appname):
    db = DatabaseManager(appname)
    db.drop()
    db.drop_user()
    return HttpResponse("", status=200)
