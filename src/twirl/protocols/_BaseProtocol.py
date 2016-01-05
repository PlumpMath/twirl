#


class BaseProtocol(object):
    def connectionMade(self):
        raise NotImplementedError()

    def dataReceived(self, data):
        raise NotImplementedError()
