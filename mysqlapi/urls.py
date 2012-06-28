from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    url(r'^resources/$', 'mysqlapi.api.views.create_database'), #post
    url(r'^resources/(?P<name>[\w-]+)/$', 'mysqlapi.api.views.drop_database'), #delete
    url(r'^resources/(?P<name>[\w-]+)/$', 'mysqlapi.api.views.create_user'), #post
    url(r'^resources/(?P<name>[\w-]+)/$', 'mysqlapi.api.views.create_user_or_drop_database'), #put
    url(r'^resources/(?P<name>[\w-]+)/export/$', 'mysqlapi.api.views.export'), #get
    url(r'^resources/(?P<name>[\w-]+)/hostname/(?P<hostname>[\w-.]+)/$', 'mysqlapi.api.views.drop_user'), #delete
)
