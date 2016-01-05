#

import pyuv

from twirl import Deferred


class Resolver(object):
    def __init__(self, loop):
        self._loop = loop
                 
    def lookupAddress(self, address, d=None):
        """ Lookup A record(s)
        """
        if d is None:
            d = Deferred()
            d.pause()
        #
        def callback2(result, errorno):
            d.callback(result)
        #
        pyuv.dns.getaddrinfo(self._loop, address, callback=callback2)
        #
        return d

    def lookupMailExchange(self, mx):
        """ Lookup MX record(s)
        """
        pass



