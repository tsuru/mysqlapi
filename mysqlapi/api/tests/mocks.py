class FakeEC2Client(object):

    def __init__(self, *args, **kwargs):
        self.actions = []

    def run(self, instance):
        self.actions.append("run instance %s" % instance.name)
        instance.ec2_id = "i-029"
        return True

    def terminate(self, instance):
        self.actions.append("terminate instance %s" % instance.name)
        return True

    def get(self, instance):
        self.actions.append("get instance %s" % instance.name)
        instance.host = "127.0.0.1"
        instance.state = "running"
        return True

    def authorize(self, instance):
        self.actions.append("authorize instance %s" % instance.name)
        return True

    def unauthorize(self, instance):
        self.actions.append("unauthorize instance %s" % instance.name)
        return True


class FakeEC2ClientPendingInstance(object):

    def __init__(self):
        self.actions = []

    def get(self, instance):
        self.actions.append("get instance %s" % instance.name)
        instance.host = ""
        instance.state = "pending"
        return True


class MultipleFailureEC2Client(FakeEC2Client):

    def __init__(self, times, *args, **kwargs):
        self.times = times
        self.failures = 0
        super(MultipleFailureEC2Client, self).__init__(*args, **kwargs)

    def get(self, instance):
        if self.failures < self.times:
            self.failures += 1
            return False
        return super(MultipleFailureEC2Client, self).get(instance)
