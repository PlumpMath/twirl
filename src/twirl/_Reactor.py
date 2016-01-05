#!/usr/bin/python

import logging 
import signal

import pyuv

from twirl.names import Resolver


class Reactor(object):

    def __init__(self, loop=None):
        self.__log = logging.getLogger("twirl.reactor")
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

    def connectTCP(self, ip, port, factory, timeout=30, bindAddress=None):
        self.__log.debug("connectTCP: ip = {ip!r}".format(ip=ip))
        #
        p = factory.buildProtocol(addr=(ip, port))
        #
        tcp = pyuv.TCP(self._loop)
        p.transport = tcp
        #
        if bindAddress is not None:
            tcp.bind((bindAddress, port))
        #
        def connect_cb(tcp_handle, error):
            if error:
                reason = pyuv.errno.strerror(error)
                self.__log.error(reason)
                p.connectionLost(reason=reason)
            else:
                p.connectionMade()
                #
                def read_cb(tcp_handle, data, error):
                    if error:
                        reason = pyuv.errno.strerror(error)
                        self.__log.error(reason)
                        p.connectionLost(reason=reason)
                    else:
                        p.dataReceived(data)
                #
                tcp.start_read(read_cb)
        #
        tcp.connect((ip, port), connect_cb)
        #
        return tcp

    def callLater(self, delay, cb, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        #
        timer = pyuv.Timer(self._loop)
        #
        def timer_cb(timer_handle):
            timer_handle.stop()
            #
            cb(*args, **kwargs)
        #
        timer.start(timer_cb, delay, delay)
        #
        return timer

    def createTTY(self, stream, protocol):
        fd = stream.fileno()
        print fd
        #
        p = protocol()
        #
        tty = pyuv.TTY(self._loop, fd, True)
        #
        p.transport = tty
        #
        def read_cb(handle, data, error):
            if error:
                reason = pyuv.errno.strerror(error)
                self.__log.error(reason)
                p.connectionLost(reason=reason)            
            else:
                if data is None:
                    handle.close()
                else:
                    print("C> {data!r}".format(data=data))
        #                 
        tty.start_read(read_cb)
        #
        print tty
        return tty
