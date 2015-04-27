# Copyright 2013 mysqlapi authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import Queue
import threading

model_class = None


class InstanceQueue(object):

    def __init__(self):
        self._queue = Queue.Queue()
        self._closed = False
        self._sem = threading.Semaphore()

    @property
    def closed(self):
        self._sem.acquire()
        closed = self._closed
        self._sem.release()
        return closed

    def close(self):
        self._sem.acquire()
        self._closed = True
        self._sem.release()

    def get(self, *args, **kwargs):
        return self._queue.get(*args, **kwargs)

    def put(self, *args, **kwargs):
        self._queue.put(*args, **kwargs)


class DatabaseCreator(threading.Thread):

    def __init__(self, manager_cls, ec2_client, user="root", password=""):
        super(DatabaseCreator, self).__init__()
        self.DatabaseManager = manager_cls
        self.ec2_client = ec2_client
        self.user = user
        self.password = password
        self.daemon = True

    def _error(self, exc, instance):
        self.ec2_client.unauthorize(instance)
        self.ec2_client.terminate(instance)
        instance.state = "error"
        instance.reason = unicode(exc)
        instance.save()

    def run(self):
        while not _instance_queue.closed:
            try:
                instance = _instance_queue.get(timeout=2)
            except Queue.Empty:
                continue
            if not self.ec2_client.get(instance):
                _instance_queue.put(instance)
                continue
            if not self.ec2_client.authorize(instance):
                self._error("Failed to authorize access to the instance.",
                            instance)
                continue
            try:
                db = self.DatabaseManager(instance.name,
                                          host=instance.host,
                                          user=self.user,
                                          password=self.password)
                db.create_database()
                instance.save()
            except Exception as exc:
                self._error(exc, instance)

    def stop(self):
        _instance_queue.close()
        self.join()

_instance_queue = InstanceQueue()


def build_queue():
    for instance in model_class.objects.filter(state="pending", shared=False):
        enqueue(instance)


def reset_queue():
    global _instance_queue
    _instance_queue = InstanceQueue()
    build_queue()


def enqueue(instance):
    _instance_queue.put(instance)


def close_queue():
    _instance_queue.close()


def set_model(cls):
    global model_class
    model_class = cls


def start_creator(manager_class, ec2_client):
    t = DatabaseCreator(manager_class, ec2_client)
    t.start()
    return t
