import boto

from boto.ec2.regioninfo import RegionInfo
from boto.exception import EC2ResponseError
from django.conf import settings


class Client(object):

    def __init__(self):
        self._ec2_conn = None

    @property
    def ec2_conn(self):
        if not self._ec2_conn:
            self._ec2_conn = boto.connect_ec2(
                aws_access_key_id=settings.EC2_ACCESS_KEY,
                aws_secret_access_key=settings.EC2_SECRET_KEY,
                region=RegionInfo(endpoint=settings.EC2_ENDPOINT),
                is_secure=False,
                port=settings.EC2_PORT,
                path=settings.EC2_PATH,
            )
        return self._ec2_conn

    def run(self, instance):
        try:
            reservation = self.ec2_conn.run_instances(
                settings.EC2_AMI,
                key_name=settings.EC2_KEY_NAME,
                security_groups=["default"],
            )
            instance.ec2_id = reservation.instances[0].id
            instance.save()
            return True
        except EC2ResponseError:
            # TODO (fsouza): skip this silenciator pattern, log the error! ;)
            return False

    def terminate(self, instance):
        terminated = self.ec2_conn.terminate_instances(
                                instance_ids=[instance.ec2_id])
        if instance.ec2_id in [inst.id for inst in terminated]:
            instance.delete()
            return True
        return False

    def get(self, instance):
        reservation = self.ec2_conn.get_all_instances(instance.ec2_id)
        ec2_instance = reservation[0].instances[0]
        if ec2_instance.ip_address != ec2_instance.private_ip_address:
            instance.state = ec2_instance.state
            instance.host = ec2_instance.ip_address
            instance.save()
            return True
        return False
