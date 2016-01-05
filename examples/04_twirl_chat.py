#!/usr/bin/python

import sys
import logging
import random

from twirl import Reactor, Factory, Deferred
from twirl.protocols import LineReceiver

irc_servers = {
    "freenode": [
        "adams.freenode.net",        # ???
        "barjavel.freenode.net",     # ???
        "calvino.freenode.net",      # Milan, IT
        "cameron.freenode.net",      # Vilnius, LT
        "hitchcock.freenode.net",    # Sofia, BG
        "hobana.freenode.net",       # Bucharest, RO
        "holmes.freenode.net",       # London, UK
        "kornbluth.freenode.net",    # Frankfurt, DE
        "leguin.freenode.net",       # Umea, SE
        "orwell.freenode.net",       # Amsterdam, NL
        "rajaniemi.freenode.net",    # Helsinki, FI
        "sendak.freenode.net",       # Vilnius, LT
        "sinisalo.freenode.net",     # Stockholm, SE
        "verne.freenode.net",        # Amsterdam, NL
        "wilhelm.freenode.net",      # Haarlem, NL
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
        self.reactor.callLater(10.0, self.irc_ping)

    def irc_register(self, username, display="Unknown"):
        self.__log.debug("Register user {username!r}".format(username=username))
        #
        #self.transport.write("PASS *\r\n")
        self.transport.write("NICK {username}\r\n".format(username=username))
        self.transport.write("USER {username} 0 * :{display}\r\n".format(username=username, display=display))

    def irc_ping(self, server=None):
        self.__log.debug("Send ping on {server!r}".format(server=server))
        #
        if server is None:
            server = self.server
        #
        self.transport.write("PING :{server}\r\n".format(server=server))
        #
        self.reactor.callLater(10.0, self.irc_ping)

    def sendMessage(self, username, msg):
        self.__log.info("Send message ")
        self.transport.write("PRIVMSG {username} :{msg}\r\n".format(username=username, msg=msg))

    def processCommand(self, prefix, command, params):
        self.__log.debug("prefix = {prefix!r}, command = {command!r}, params = {params!r}".format(prefix=prefix, command=command, params=params))
        #
        if prefix is not None:
            # remove 
            prefix = prefix[1:]
            #
            servername = prefix
            nickname = prefix
            #
            if "@" in prefix:
                nickname, host = prefix.split("@", 1)
                if "!" in nickname:
                    nickname, user = nickname.split("!", 1)
                else:
                    user = None
            else:
                host = None
        #
        self.__log.debug("Parse server name: nickname = {nickname!r}".format(nickname=nickname))
        #
        if command == "PRIVMSG":
            msg = "Hello, after parsing we have !!!"
            self.sendMessage(username=nickname, msg=msg)
        elif command == "451":
            # Not registered
            self.irc_register("vit1252")
        elif command == "PING":
            self.sendPong()
        elif command == "ERROR":
            self.__log.error("Error !!!")
        elif command == "PONG":
            pass
        elif command == "NOTICE":
            pass
        else:
            self.__log.error("Unsupported command")

    def sendPong(self):
        self.transport.write("PONG\r\n".format())

    def processMessage(self, msg):
        # Step 1. Prefix checkin
        prefix = None
        if msg.startswith(":"):
            prefix, msg = msg.split(" ", 1)
        #
        command, params = msg.split(" ", 1)
        self.processCommand(prefix, command, params)

    def lineReceived(self, line):
        self.__log.info("Server send line {line!r}".format(line=line))
        self.processMessage(msg=line)

    def connectionLost(self, reason):
        self.__log.debug("Connection is shut down")


class CommandProtocol(LineReceiver):
    def __init__(self, app):
        LineReceiver.__init__(self)
        self.delimiter = b'\n'
        self.__log = logging.getLogger('app.tty.command')
        self.app = app

    def lineReceived(self, line):
        self.__log.info("Client comand {line!r}".format(line=line))
        #
        cmd, args = line.split(" ", 1)
        #
        if cmd == '/msg':
            self.__log.info("Send message")
            app.sendMessage("vit1251", args)
        elif cmd == '/register':
            self.__log.info("Send registration")
            app.register(args)
        elif cmd == '/join':
            pass
        else:
            sys.stdout.write("WARN: Bad command `{cmd}`!".format(cmd=cmd))


class IRCClientProtocolFactory(object):
    def __init__(self):
        self.conns = []

    def buildProtocol(self, addr):
        p = IRCClientProtocol()
        p.reactor = self.reactor
        self.conns.append(p)
        return p


class Application(object):
    def __init__(self):
        self.__log = logging.getLogger('app')
        self.__reactor = Reactor.default_reactor()
        self.__resolver = self.__reactor.createResolver()
        self.__tty = None
        self.__factory = None

    def dispose(self):
        if self.__tty is not None:
            self.__tty.close()

    def selectServers(self, network):
        if network in irc_servers:
            return irc_servers[network]
        return []

    def selectServer(self, network):
        servers = self.selectServers(network)
        return random.choice(servers)

    def sendMessage(self, user, msg):
        for conn in self.__factory.conns:
            conn.sendMessage(user, msg)

    def register(self, user):
        for conn in self.__factory.conns:
            conn.register(user)

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
        self.__factory = IRCClientProtocolFactory()
        self.__factory.reactor = self.__reactor
        #
        self.__reactor.connectTCP(ip=ip, port=port, factory=self.__factory, timeout=30, bindAddress=None)

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
        self.__tty = self.__reactor.createTTY(stream=sys.stdin, protocol=CommandProtocol(app=self))
        #
        self.__reactor.callLater(1.0, self.connectionCreate)
        self.__reactor.run()


if __name__ == "__main__":
    #logging.basicConfig(filename="debug.log", level=logging.DEBUG)
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    #
    app = Application()
    try:
        app.run()
    finally:
        app.dispose()

