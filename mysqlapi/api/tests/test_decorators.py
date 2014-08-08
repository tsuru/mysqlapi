# -*- coding: utf-8 -*-

# Copyright 2014 mysqlapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import base64
import os

from django import test

from mysqlapi.api.decorators import basic_auth_required


class BasicAuthTestCase(test.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.factory = test.RequestFactory()

    def setenvs(self):
        os.environ["API_USERNAME"] = self.username = "api"
        os.environ["API_PASSWORD"] = self.password = "abc123"

    def delenvs(self):
        del os.environ["API_USERNAME"], os.environ["API_PASSWORD"]

    def get_fn(self):
        calls = {"c": 0}

        @basic_auth_required
        def fn(request):
            calls["c"] += 1
        return fn, calls

    def test_auth_no_password(self):
        fn, calls = self.get_fn()
        fn(None)
        self.assertEqual(1, calls["c"])

    def test_auth_success(self):
        self.setenvs()
        self.addCleanup(self.delenvs)
        fn, calls = self.get_fn()
        request = self.factory.get("/")
        token = base64.b64encode(self.username + ":" + self.password)
        request.META["HTTP_AUTHORIZATION"] = "basic " + token
        fn(request)
        self.assertEqual(1, calls["c"])

    def test_auth_no_authorization_info(self):
        self.setenvs()
        self.addCleanup(self.delenvs)
        fn, calls = self.get_fn()
        request = self.factory.get("/")
        resp = fn(request)
        self.assertEqual(401, resp.status_code)
        self.assertEqual("you're not authorized", resp.content)
        self.assertEqual(0, calls["c"])

    def test_auth_not_basic_authorization(self):
        self.setenvs()
        self.addCleanup(self.delenvs)
        fn, calls = self.get_fn()
        request = self.factory.get("/")
        token = base64.b64encode(self.username + ":" + self.password)
        request.META["HTTP_AUTHORIZATION"] = "bearer " + token
        resp = fn(request)
        self.assertEqual(401, resp.status_code)
        self.assertEqual("you're not authorized", resp.content)
        self.assertEqual(0, calls["c"])

    def test_auth_wrong_user(self):
        self.setenvs()
        self.addCleanup(self.delenvs)
        fn, calls = self.get_fn()
        request = self.factory.get("/")
        token = base64.b64encode(self.username + "aa:" + self.password)
        request.META["HTTP_AUTHORIZATION"] = "basic " + token
        resp = fn(request)
        self.assertEqual(401, resp.status_code)
        self.assertEqual("you're not authorized", resp.content)
        self.assertEqual(0, calls["c"])

    def test_auth_wrong_password(self):
        self.setenvs()
        self.addCleanup(self.delenvs)
        fn, calls = self.get_fn()
        request = self.factory.get("/")
        token = base64.b64encode(self.username + ":" + self.password + "aa")
        request.META["HTTP_AUTHORIZATION"] = "basic " + token
        resp = fn(request)
        self.assertEqual(401, resp.status_code)
        self.assertEqual("you're not authorized", resp.content)
        self.assertEqual(0, calls["c"])
