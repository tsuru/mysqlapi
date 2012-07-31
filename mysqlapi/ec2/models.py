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

    def run_instance(self, instance):
        try:
            reservation = self.ec2_conn.run_instances(
                settings.EC2_AMI,
                key_name=settings.EC2_KEY_NAME,
                security_groups=["default"],
            )
            instance.instance_id = reservation.instances[0].id
            instance.save()
            return True
        except EC2ResponseError:
            # TODO (fsouza): skip this silenciator pattern, log the error! ;)
            return False
