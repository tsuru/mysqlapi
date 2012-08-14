# -*- coding: utf-8 -*-
import crane_ec2

from mysqlapi.api.models import DatabaseManager
from mysqlapi.api.creator import start_creator


def start():
    client = crane_ec2.Client()
    start_creator(DatabaseManager, client)

start()
