from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    url(r'^resources/$', 'mysqlapi.api.create'),
    url(r'^resources/(?P<appname>[\w-]+)/$', 'mysqlapi.api.destroy'),
)
