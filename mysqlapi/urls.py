from django.conf.urls import patterns, url

from mysqlapi.api.views import CreateUserOrDropDatabase, Healthcheck


urlpatterns = patterns('',
    url(r'^resources/$', 'mysqlapi.api.views.create_database'),  # post
    url(r'^resources/(?P<name>[\w-]+)/$', CreateUserOrDropDatabase.as_view()),  # post and delete
    url(r'^resources/(?P<name>[\w-]+)/export/$', 'mysqlapi.api.views.export'),  # get
    url(r'^resources/(?P<name>[\w-]+)/status/$', Healthcheck.as_view()),  # get
    url(r'^resources/(?P<name>[\w-]+)/hostname/(?P<hostname>[\w.]+)/$', 'mysqlapi.api.views.drop_user'),  # delete
)
