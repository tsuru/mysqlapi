from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    url(r'^resources/$', 'mysqlapi.api.views.create_database'),
    url(r'^resources/(?P<appname>[\w-]+)/$', 'mysqlapi.api.views.drop_database'),
    url(r'^resources/(?P<appname>[\w-]+)/export/$', 'mysqlapi.api.views.export'),
)
