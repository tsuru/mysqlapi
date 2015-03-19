# Copyright 2015 mysqlapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import base64
import functools
import os

from django import http


def basic_auth_required(view):
    expected_username = os.environ.get("API_USERNAME", "mysql")
    expected_password = os.environ.get("API_PASSWORD")

    @functools.wraps(view)
    def fn(request, *args, **kwargs):
        unauthorized_resp = http.HttpResponse("you're not authorized")
        unauthorized_resp.status_code = 401
        if not expected_password:
            return view(request, *args, **kwargs)
        auth = request.META.get("HTTP_AUTHORIZATION")
        if not auth:
            return unauthorized_resp
        kind, data = auth.split()
        if kind.lower() != "basic":
            return unauthorized_resp
        username, password = base64.b64decode(data).split(":")
        if username == expected_username and password == expected_password:
            return view(request, *args, **kwargs)
        return unauthorized_resp
    return fn
