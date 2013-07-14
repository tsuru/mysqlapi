#mysqlapi

[![Build Status](https://secure.travis-ci.org/globocom/mysqlapi.png?branch=master)](http://travis-ci.org/globocom/mysqlapi)

This is a service API for MySQL, used for [tsuru](https://github.com/globocom/tsuru).

Installation
------------

First, create an app in tsuru:

    $> tsuru app-create mysql-api python

Add the returned remote to your repository:

    $> git remote add tsuru git@yourremote.git

When the app is in `started` state, push the code:

    $> git push tsuru master

Basic set up
------------

In order to have mysql API ready to receive requests, we need some bootstrap stuff.

First export the django settings variable:

    $> tsuru env-set --app mysql-api DJANGO_SETTINGS_MODULE=mysqlapi.settings

Now gunicorn is able to run with our wsgi.py configuration.
After that, we need to run syncdb:

    $> tsuru run --app mysql-api -- python manage.py syncdb --noinput

Now we're ready to move on.

Choose your configuration mode
------------------------------

There are two modes to configure the API usage behavior:

- `shared`: this configuration forces all applications to share the same mysql installation, in this mode, mysql API
will create a new user and a new database when added/binded by an app.
- `dedicated`: every app using mysql will have a single vm for it's usage, in this mode, mysql API will create a vm,
install everything needed to run mysql based on a predefined AMI and create a user and password.

Everything that is needed by the application to connect with mysql is provided automatically by tsuru, using environment variables,
e.g. when you add/bind your app with mysql service, tsuru will export all environment variables returned by mysql API.

Shared Configuration
--------------------

To run the API in shared mode, you'll need some setup. First export the needed variables:

    $> tsuru env-set --app mysql-api MYSQLAPI_SHARED_SERVER=mysqlhost.com

If the shared mysql database is installed in the sabe vm that the app is, you can use `localhost` for `MYSQLAPI_SHARED_SERVER`,
but you'll also need to set up a externally accessible endpoint to be used by the apps that are using the service:

    $> tsuru env-set --app mysql-api MYSQLAPI_SHARED_SERVER_PUBLIC_HOST=publichost.com

** Important: if your tsuru setup is using ELB, you shouldn't use it's address here, the LB keeps the connections alive, what will
cause mysql to eventually fail, you should use your application unit address.

Try your configuration
----------------------

You can try if the previous configuration worked using curl:

    $> curl -d 'name=myapp' http://ec2-23-23-67-196.compute-1.amazonaws.com/resources

This call is equivalente to tsuru service-add xx yy and will return 201 if everything goes ok.

If there are any problems, be welcome to report an issue :)
