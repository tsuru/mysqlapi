# Copyright 2014 mysqlapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from django.conf.urls import patterns, url

from mysqlapi.api.decorators import basic_auth_required
from mysqlapi.api.views import (CreateUserOrDropDatabase,
                                CreateDatabase, Healthcheck)

urlpatterns = patterns('',
                       url(r'^resources$',
                           basic_auth_required(CreateDatabase.as_view())),
                       url(r'^resources/(?P<name>[\w-]+)$',
                           basic_auth_required(CreateUserOrDropDatabase.as_view())),
                       url(r'^resources/(?P<name>[\w-]+)/export$',
                           'mysqlapi.api.views.export'),
                       url(r'^resources/(?P<name>[\w-]+)/status$',
                           basic_auth_required(Healthcheck.as_view())),
                       url(r'^resources/(?P<name>[\w-]+)/hostname/' +
                           '(?P<hostname>[\w.]+)$',
                           'mysqlapi.api.views.drop_user'),
                       )
