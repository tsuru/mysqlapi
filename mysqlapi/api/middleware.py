# Copyright 2015 mysqlapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import sys
import traceback


class ExceptionLoggingMiddleware(object):

    def process_exception(self, request, exception):
        sys.stderr.write("Failed to handle request {}".format(request.path))
        traceback.print_exc(file=sys.stderr)
