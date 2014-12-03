#mysqlapi

[![Build Status](https://secure.travis-ci.org/tsuru/mysqlapi.png?branch=master)](http://travis-ci.org/tsuru/mysqlapi)

This is a service API for MySQL, used for [tsuru](https://github.com/globocom/tsuru).

Installation
------------

In order to have mysql API ready to receive requests, we need some bootstrap stuff.

The first step is to install the dependencies. Let's use pip to do it:

    $ pip install -r requirements.txt

Now we need to run syncdb:

    $ python manage.py syncdb

Exporting enviroment variable to set the settings location:

    $ export DJANGO_SETTINGS_MODULE=mysqlapi.settings


Choose your configuration mode
------------------------------

There are three modes to configure the API usage behavior:

- `shared`: this configuration forces all applications to share the same mysql
  installation, in this mode, mysql API will create a new user and a new
  database when added/binded by an app.
- `dedicated (on-demmand)`: every app using mysql will have a single vm for
  it's usage, in this mode, mysql API will create a vm, install everything
  needed to run mysql based on a predefined AMI and create a user and password.
- `dedicated (pre-provisioned)`: every app using mysql will have a single MySQL
  instance, pre-provisioned.

Everything that is needed by the application to connect with mysql is provided
automatically by tsuru, using environment variables, e.g. when you add/bind
your app with mysql service, tsuru will export all environment variables
returned by mysql API.

Shared Configuration
--------------------

To run the API in shared mode, is needed to have a mysql installed and export
two enviroment variables.

One variable is to set the mysql host. If the shared mysql database is
installed in the sabe vm that the app is, you can use `localhost` for
``MYSQLAPI_SHARED_SERVER``, but you'll also need to set up a externally
accessible endpoint to be used by the apps that are using the service:

    $ MYSQLAPI_SHARED_SERVER=mysqlhost.com
    $ MYSQLAPI_SHARED_SERVER_PUBLIC_HOST=publichost.com

Running the api
---------------

    $ gunicorn wsgi -b 0.0.0.0:8888

Try your configuration
----------------------

You can try if the previous configuration worked using curl:

    $> curl -d 'name=myapp' http://youmysqlapi.com/resources

This call is the same as to ``tsuru service-add <service-name>
<service-instance-name>`` and will return 201 if everything goes ok.

If there are any problems, be welcome to report an issue :)
