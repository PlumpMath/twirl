#!/usr/bin/python

import pyuv
import signal

from twirl.names import Resolver


class Reactor(object):

    def __init__(self, loop=None):
        self._loop = loop

    @staticmethod
    def default_reactor():
        loop = pyuv.Loop.default_loop()
        r = Reactor(loop=loop)
        r._initialize()
        return r

    def createResolver(self):
        return Resolver(loop=self._loop)

    def _on_sig_int_cb(self):
        print "Ctrl+C"

    def _initialize(self):
        signal_h = pyuv.Signal(self._loop)
        signal_h.start(self._on_sig_int_cb, signal.SIGINT)

    def stop(self):
        self._loop.stop()

    def run(self):
        self._loop.run(pyuv.UV_RUN_DEFAULT)

    def listenUDP(self, port, protocol, interface='0.0.0.0', maxPacketSize=8192):
        """
        """
        #
        p = protocol()
        #
        udp = pyuv.UDP(self._loop) # AF_UNSPEC
        udp.bind((interface, port))
        #
        p.transport = udp
        #
        p.doStart()
        #
        return udp
