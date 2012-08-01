from boto.ec2.instance import Instance, Reservation
from boto.exception import EC2ResponseError


class FakeEC2Conn(object):

    def __init__(self, time_to_fail=1, *args, **kwargs):
        self.instances = []
        self.terminated = []
        self.args = args
        self.kwargs = kwargs
        self.time_to_fail = time_to_fail

    def run_instances(self, ami, *args, **kwargs):
        self.instances.append("instance with ami %s and key %s and groups %s" % (
            ami,
            kwargs["key_name"],
            ", ".join(kwargs["security_groups"])
        ))
        instance = Instance()
        instance.id = 'i-00000302'
        reservation = Reservation()
        reservation.instances = [instance]
        return reservation

    def terminate_instances(self, instance_ids):
        self.terminated.extend(instance_ids)
        instances = []
        for instance_id in instance_ids:
            instance = Instance()
            instance.id = instance_id
            instances.append(instance)
        return instances


class FailingEC2Conn(FakeEC2Conn):

    def run_instances(self, *args, **kwargs):
        raise EC2ResponseError(status=500, reason="Failed")

    def terminate_instances(self, instance_ids):
        return []
