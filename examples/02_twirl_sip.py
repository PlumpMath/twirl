#!/usr/bin/python

import sys
import logging

from twirl import Reactor
from twirl.protocols.sip import SIPProtocol


class CustomSIPProtocol(SIPProtocol):
    def handle_request(self, message, addr):
        print message

    def handle_response(self, message, addr):
        print message


class Application(object):
    def __init__(self):
        self.__reactor = Reactor.default_reactor()

    def run(self):
        self.__reactor.listenUDP(port=5060, protocol=CustomSIPProtocol, interface='0.0.0.0', maxPacketSize=8192)
        self.__reactor.run()


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    #
    app = Application()
    app.run()
