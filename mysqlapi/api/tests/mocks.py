from boto.ec2.instance import Instance, Reservation


class FakeEC2Conn(object):

    def __init__(self, *args, **kwargs):
        self.instances = []
        self.args = args
        self.kwargs = kwargs

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
