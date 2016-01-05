#!/usr/bin/python

import sys
import logging
import random

from twirl import Reactor, Factory, Deferred
from twirl.protocols import LineReceiver

irc_servers = {
    "freenode": [
        "adams.freenode.net",
        "barjavel.freenode.net",
#Milan, IT	calvino.freenode.net	IPv4, IPv6
#Vilnius, LT	cameron.freenode.net	IPv4, IPv6
#Sofia, BG	hitchcock.freenode.net	IPv4
#Bucharest, RO	hobana.freenode.net	IPv4, IPv6
#London, UK	holmes.freenode.net	IPv4, IPv6
#Frankfurt, DE	kornbluth.freenode.net	IPv4
#Umea, SE	leguin.freenode.net	IPv4, IPv6
#Amsterdam, NL	orwell.freenode.net	IPv4
#Helsinki, FI	rajaniemi.freenode.net	IPv4, IPv6
#Vilnius, LT	sendak.freenode.net	IPv4
#Stockholm, SE	sinisalo.freenode.net	IPv4, IPv6
#Amsterdam, NL	verne.freenode.net	IPv4
#Haarlem, NL	wilhelm.freenode.net
    ]
}

class IRCClientProtocol(LineReceiver):
    def __init__(self, server=None):
        LineReceiver.__init__(self)
        #
        self.__log = logging.getLogger('twirl.protocol.irc')
        #
        self.server = server

    def connectionMade(self):
        self.__log.debug("Connection is made")
        self.reactor.callLater(5.0, self.irc_register, args=["vit1251"])
        self.reactor.callLater(10.0, self.irc_ping)

    def irc_register(self, username):
        self.__log.debug("Register user {username!r}".format(username=username))
        #
        #self.transport.write("PASS *\r\n")
        self.transport.write("NICK vit1252\r\n")
        self.transport.write("USER vit1252 0 * :Vitold S\r\n")

    def irc_ping(self, server=None):
        self.__log.debug("Send ping on {server!r}".format(server=server))
        #
        if server is None:
            server = self.server
        #
        self.transport.write("PING :{server}\r\n".format(server=server))
        #
        self.reactor.callLater(10.0, self.irc_ping)

    def lineReceived(self, line):
        self.__log.info("Server send line {line!r}".format(line=line))
        #
        sys.stdout.write("S> {line}\n".format(line=line))

    def connectionLost(self, reason):
        self.__log.debug("Connection is shut down")


class CommandProtocol(LineReceiver):
    def lineReceived(self, line):
        self.__log.info("Client comand {line!r}".format(line=line))


class IRCClientProtocolFactory(object):
    def buildProtocol(self, addr):
        p = IRCClientProtocol()
        p.reactor = self.reactor
        return p


class Application(object):
    def __init__(self):
        self.__log = logging.getLogger('app')
        self.__reactor = Reactor.default_reactor()
        self.__resolver = self.__reactor.createResolver()
        self.__tty = None
    
    def selectServers(self, network):
        if network in irc_servers:
            return irc_servers[network]
        return []

    def selectServer(self, network):
        servers = self.selectServers(network)
        return random.choice(servers)

    def startConnection(self, addrs):
        if addrs is None:
            self.connectionCreate()
            return 
        #
        ip = None
        for addr in addrs:
            ip = addr.sockaddr[0]
            break
        port = 6666
        #
        self.__log.debug("Start connection on {ip!r} port {port!r}".format(ip=ip, port=port))
        #
        factory = IRCClientProtocolFactory()
        factory.reactor = self.__reactor
        #
        self.__reactor.connectTCP(ip=ip, port=port, factory=factory, timeout=30, bindAddress=None)

    def resolveServer(self, host):
        d = Deferred()        # TODO - prepare deffer reaction or unpause later when else
        d.addCallback(self.startConnection)
        #
        self.__resolver.lookupAddress(host, d=d)

    def connectionCreate(self):
        server = self.selectServer(network="freenode")
        self.resolveServer(server)

    def run(self):
        """ Create application inner reactor
        """
        self.__tty = self.__reactor.createTTY(stream=sys.stdin, protocol=CommandProtocol)
        #
        self.__reactor.callLater(1.0, self.connectionCreate)
        self.__reactor.run()


if __name__ == "__main__":
    #logging.basicConfig(filename="debug.log", level=logging.DEBUG)
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    #
    app = Application()
    app.run()

        