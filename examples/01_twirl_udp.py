#!/usr/bin/python

from twirl import Reactor
from twirl.protocols import DatagramProtocol


class CustomProtocol(DatagramProtocol):
    def datagramReceived(self, datagram, addr):
        print datagram, addr


class Application(object):
    def __init__(self):
        self.__reactor = Reactor.default_reactor()

    def run(self):
        self.__reactor.listenUDP(port=5060, protocol=CustomProtocol, interface='0.0.0.0', maxPacketSize=8192)
        self.__reactor.run()


if __name__ == "__main__":
    app = Application()
    app.run()
