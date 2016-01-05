

class Factory(object):
    def __init__(self):
        pass

    def buildProtocol(self, addr):
        raise NotImplementedError()
