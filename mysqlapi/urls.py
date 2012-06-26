from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    url(r'^resources/$', 'mysqlapi.api.views.create'),
    url(r'^resources/(?P<appname>[\w-]+)/$', 'mysqlapi.api.views.drop'),
    url(r'^resources/(?P<appname>[\w-]+)/export/$', 'mysqlapi.api.views.export'),
)
