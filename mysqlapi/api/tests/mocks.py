class FakeEC2Client(object):

    def __init__(self, *args, **kwargs):
        self.actions = []

    def run(self, instance):
        self.actions.append("run instance %s" % instance.name)
        return True

    def get(self, instance):
        self.actions.append("get instance %s" % instance.name)
        return True
