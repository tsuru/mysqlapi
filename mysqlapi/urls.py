from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    url(r'^resources/$', 'mysqlapi.api.views.create_database'),
    url(r'^resources/(?P<name>[\w-]+)/$', 'mysqlapi.api.views.drop_database'),
    url(r'^resources/(?P<name>[\w-]+)/export/$', 'mysqlapi.api.views.export'),
    url(r'^resources/(?P<name>[\w-]+)/export/$', 'mysqlapi.api.views.export'),
    url(r'^resources/(?P<name>[\w-]+)/hostname/(?P<hostname>[\w-.]+)/$', 'mysqlapi.api.views.drop_user'),
)
