#

import pyuv

from twirl import Deferred


class Resolver(object):
    def __init__(self, loop):
        self._loop = loop
                 
    def lookupAddress(self, address):
        """ Lookup A record(s)
        """
        d = Deferred()
        #
        def callback2(result, errorno):
            for ai in result:
                print ai
        #
        pyuv.dns.getaddrinfo(self._loop, address, callback=callback2)
        #
        return d

    def lookupMailExchange(self, mx):
        """ Lookup MX record(s)
        """
        pass



