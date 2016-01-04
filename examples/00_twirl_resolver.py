#!/usr/bin/python

from twirl import Reactor


class Application(object):
    def __init__(self):
        self.__reactor = Reactor.default_reactor()

    def printResult(self, r, domainname):
        print r, domainname

    def run(self):
        resolver = self.__reactor.createResolver()
        #
        domainname = "yandex.ru"
        d = resolver.lookupAddress(domainname)
        d.addCallback(self.printResult, domainname)
        #
        self.__reactor.run()


if __name__ == "__main__":
    app = Application()
    app.run()
