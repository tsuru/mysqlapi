from django.conf.urls import patterns, url

from mysqlapi.api.views import (CreateUserOrDropDatabase,
                                CreateDatabase, Healthcheck)


urlpatterns = patterns('',
                       url(r'^resources$',
                           CreateDatabase.as_view()),  # post
                       url(r'^resources/(?P<name>[\w-]+)$',
                           CreateUserOrDropDatabase.as_view()),
                       url(r'^resources/(?P<name>[\w-]+)/export$',
                           'mysqlapi.api.views.export'),  # get
                       url(r'^resources/(?P<name>[\w-]+)/status$',
                           Healthcheck.as_view()),  # get
                       url(r'^resources/(?P<name>[\w-]+)/hostname/' +
                           '(?P<hostname>[\w.]+)$',
                           'mysqlapi.api.views.drop_user'),
                       )
