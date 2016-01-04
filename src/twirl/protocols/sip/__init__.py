#

import logging

from twirl.protocols import LineReceiver, DatagramProtocol

PORT=5060

statusCodes = {
    100: "Trying",
    180: "Ringing",
    181: "Call Is Being Forwarded",
    182: "Queued",
    183: "Session Progress",

    200: "OK",

    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Moved Temporarily",
    303: "See Other",
    305: "Use Proxy",
    380: "Alternative Service",

    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict", # Not in RFC3261
    410: "Gone",
    411: "Length Required", # Not in RFC3261
    413: "Request Entity Too Large",
    414: "Request-URI Too Large",
    415: "Unsupported Media Type",
    416: "Unsupported URI Scheme",
    420: "Bad Extension",
    421: "Extension Required",
    423: "Interval Too Brief",
    480: "Temporarily Unavailable",
    481: "Call/Transaction Does Not Exist",
    482: "Loop Detected",
    483: "Too Many Hops",
    484: "Address Incomplete",
    485: "Ambiguous",
    486: "Busy Here",
    487: "Request Terminated",
    488: "Not Acceptable Here",
    491: "Request Pending",
    493: "Undecipherable",

    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway", # no donut
    503: "Service Unavailable",
    504: "Server Time-out",
    505: "SIP Version not supported",
    513: "Message Too Large",

    600: "Busy Everywhere",
    603: "Decline",
    604: "Does not exist anywhere",
    606: "Not Acceptable",
}

class Via(object):
    """
    A L{Via} is a SIP Via header, representing a segment of the path taken by
    the request.

    See RFC 3261, sections 8.1.1.7, 18.2.2, and 20.42.

    @ivar transport: Network protocol used for this leg. (Probably either "TCP"
    or "UDP".)
    @type transport: C{str}
    @ivar branch: Unique identifier for this request.
    @type branch: C{str}
    @ivar host: Hostname or IP for this leg.
    @type host: C{str}
    @ivar port: Port used for this leg.
    @type port C{int}, or None.
    @ivar rportRequested: Whether to request RFC 3581 client processing or not.
    @type rportRequested: C{bool}
    @ivar rportValue: Servers wishing to honor requests for RFC 3581 processing
    should set this parameter to the source port the request was received
    from.
    @type rportValue: C{int}, or None.

    @ivar ttl: Time-to-live for requests on multicast paths.
    @type ttl: C{int}, or None.
    @ivar maddr: The destination multicast address, if any.
    @type maddr: C{str}, or None.
    @ivar hidden: Obsolete in SIP 2.0.
    @type hidden: C{bool}
    @ivar otherParams: Any other parameters in the header.
    @type otherParams: C{dict}
    """

    def __init__(self, host, port=PORT, transport="UDP", ttl=None, hidden=False, received=None, rport=False, branch=None, maddr=None, **kw):
        """
        Set parameters of this Via header. All arguments correspond to
        attributes of the same name.

        To maintain compatibility with old SIP
        code, the 'rport' argument is used to determine the values of
        C{rportRequested} and C{rportValue}. If None, C{rportRequested} is set
        to True. (The deprecated method for doing this is to pass True.) If an
        integer, C{rportValue} is set to the given value.

        Any arguments not explicitly named here are collected into the
        C{otherParams} dict.
        """
        self.transport = transport
        self.host = host
        self.port = port
        self.ttl = ttl
        self.hidden = hidden
        self.received = received
        if rport is True:
            self.rportValue = None
            self.rportRequested = True
        elif rport is None:
            self.rportValue = None
            self.rportRequested = True
        elif rport is False:
            self.rportValue = None
            self.rportRequested = False
        else:
            self.rportValue = rport
            self.rportRequested = False
        self.branch = branch
        self.maddr = maddr
        self.otherParams = kw


    def _getrport(self):
        """
        Returns the rport value expected by the old SIP code.
        """
        if self.rportRequested == True:
            return True
        elif self.rportValue is not None:
            return self.rportValue
        else:
            return None


    def _setrport(self, newRPort):
        """
        L{Base._fixupNAT} sets C{rport} directly, so this method sets
        C{rportValue} based on that.

        @param newRPort: The new rport value.
        @type newRPort: C{int}
        """
        self.rportValue = newRPort
        self.rportRequested = False


    rport = property(_getrport, _setrport)

    def toString(self):
        """
        Serialize this header for use in a request or response.
        """
        s = "SIP/2.0/%s %s:%s" % (self.transport, self.host, self.port)
        if self.hidden:
            s += ";hidden"
        for n in "ttl", "branch", "maddr", "received":
            value = getattr(self, n)
            if value is not None:
                s += ";%s=%s" % (n, value)
        if self.rportRequested:
            s += ";rport"
        elif self.rportValue is not None:
            s += ";rport=%s" % (self.rport,)

        etc = self.otherParams.items()
        etc.sort()
        for k, v in etc:
            if v is None:
                s += ";" + k
            else:
                s += ";%s=%s" % (k, v)
        return s


def parseViaHeader(value):
    """
    Parse a Via header.

    @return: The parsed version of this header.
    @rtype: L{Via}
    """
    parts = value.split(";")
    sent, params = parts[0], parts[1:]
    protocolinfo, by = sent.split(" ", 1)
    by = by.strip()
    result = {}
    pname, pversion, transport = protocolinfo.split("/")
    if pname != "SIP" or pversion != "2.0":
        raise ValueError("wrong protocol or version: %r" % value)
    result["transport"] = transport
    if ":" in by:
        host, port = by.split(":")
        result["port"] = int(port)
        result["host"] = host
    else:
        result["host"] = by
    for p in params:
        # it's the comment-striping dance!
        p = p.strip().split(" ", 1)
        if len(p) == 1:
            p, comment = p[0], ""
        else:
            p, comment = p
        if p == "hidden":
            result["hidden"] = True
            continue
        parts = p.split("=", 1)
        if len(parts) == 1:
            name, value = parts[0], None
        else:
            name, value = parts
            if name in ("rport", "ttl"):
                value = int(value)
        result[name] = value
    return Via(**result)


class URL(object):
    """ A SIP URL
    """

    def __init__(self, host, username=None, password=None, port=None, transport=None, usertype=None, method=None, ttl=None, maddr=None, tag=None, other=None, headers=None):
        self.username = username
        self.host = host
        self.password = password
        self.port = port
        self.transport = transport
        self.usertype = usertype
        self.method = method
        self.tag = tag
        self.ttl = ttl
        self.maddr = maddr
        if other == None:
            self.other = []
        else:
            self.other = other
        if headers == None:
            self.headers = {}
        else:
            self.headers = headers

    def toString(self):
        l = []; w = l.append
        w("sip:")
        if self.username != None:
            w(self.username)
            if self.password != None:
                w(":%s" % self.password)
            w("@")
        w(self.host)
        if self.port != None:
            w(":%d" % self.port)
        if self.usertype != None:
            w(";user=%s" % self.usertype)
        for n in ("transport", "ttl", "maddr", "method", "tag"):
            v = getattr(self, n)
            if v != None:
                w(";%s=%s" % (n, v))
        for v in self.other:
            w(";%s" % v)
        if self.headers:
            w("?")
            w("&".join([("%s=%s" % (specialCases.get(h) or dashCapitalize(h), v)) for (h, v) in self.headers.items()]))
        return "".join(l)

    def __str__(self):
        return self.toString()

    def __repr__(self):
        return '<URL %s:%s@%s:%r/%s>' % (self.username, self.password, self.host, self.port, self.transport)


def parseURL(url, host=None, port=None):
    """Return string into URL object.

    URIs are of form 'sip:user@example.com'.
    """
    d = {}
    if not url.startswith("sip:"):
        raise ValueError("unsupported scheme: " + url[:4])
    parts = url[4:].split(";")
    userdomain, params = parts[0], parts[1:]
    udparts = userdomain.split("@", 1)
    if len(udparts) == 2:
        userpass, hostport = udparts
        upparts = userpass.split(":", 1)
        if len(upparts) == 1:
            d["username"] = upparts[0]
        else:
            d["username"] = upparts[0]
            d["password"] = upparts[1]
    else:
        hostport = udparts[0]
    hpparts = hostport.split(":", 1)
    if len(hpparts) == 1:
        d["host"] = hpparts[0]
    else:
        d["host"] = hpparts[0]
        d["port"] = int(hpparts[1])
    if host != None:
        d["host"] = host
    if port != None:
        d["port"] = port
    for p in params:
        if p == params[-1] and "?" in p:
            d["headers"] = h = {}
            p, headers = p.split("?", 1)
            for header in headers.split("&"):
                k, v = header.split("=")
                h[k] = v
        nv = p.split("=", 1)
        if len(nv) == 1:
            d.setdefault("other", []).append(p)
            continue
        name, value = nv
        if name == "user":
            d["usertype"] = value
        elif name in ("transport", "ttl", "maddr", "method", "tag"):
            if name == "ttl":
                value = int(value)
            d[name] = value
        else:
            d.setdefault("other", []).append(p)
    return URL(**d)


def cleanRequestURL(url):
    """ Clean a URL from a Request line
    """
    url.transport = None
    url.maddr = None
    url.ttl = None
    url.headers = {}


class MessageHeader(object):
    def __init__(self, name):
        self.name = name
        self.values = []

    def __getitem__(self, item):
        return self.values[item]

    def __setitem__(self, item, value):
        self.values[item] = value

    def addValue(self, value):
        self.values.append(value)
   

class MessageHeaders(object):
    def __init__(self):
        self._headers = []

    def __iter__(self):
        return iter(self._headers)

    def searchHeader(self, search, case=False):
        result = None
        for header in self._headers:
            name = header.name
            if case is False:
                name = name.lower()
            if name == search:
                return header
        return result

    def __getitem__(self, item):
        return self.searchHeader(search=item, case=False)

    def removeHeader(self, name):
        s = self.searchHeader(name)
        self._headers.remove(s)

    def addHeader(self, name, value):
        header = self.searchHeader(name)
        if header is not None:
            header.addValue(value)
        else:
            header = MessageHeader(name=name)
            header.addValue(value)
            self._headers.append(header)


class Message(object):
    """A SIP message."""

    length = None

    def __init__(self):
        self.headers = MessageHeaders()
        self.body = ""
        self.finished = 0

    def addHeader(self, name, value):
        self.headers.addHeader(name, value)
        #
        name = name.lower()
        if name == "content-length":
            self.length = int(value)

    def bodyDataReceived(self, data):
        self.body += data

    def creationFinished(self):
        if (self.length != None) and (self.length != len(self.body)):
            raise ValueError("wrong body length")
        self.finished = 1

    def toString(self):
        s = "%s\r\n" % self._getHeaderLine()
        for header in self.headers:
            for value in header.values:
                s += "{name}: {value}\r\n".format(name=header.name, value=value)
        s += "\r\n"
        s += self.body
        return s

    def _getHeaderLine(self):
        raise NotImplementedError()


class Request(Message):
    """A Request for a URI"""


    def __init__(self, method, uri, version="SIP/2.0"):
        Message.__init__(self)
        self.method = method
        if isinstance(uri, URL):
            self.uri = uri
        else:
            self.uri = parseURL(uri)
            cleanRequestURL(self.uri)

    def __repr__(self):
        return "<SIP Request %d:%s %s>" % (id(self), self.method, self.uri.toString())

    def _getHeaderLine(self):
        return "%s %s SIP/2.0" % (self.method, self.uri.toString())


class Response(Message):
    """A Response to a URI Request"""

    def __init__(self, code, phrase=None, version="SIP/2.0"):
        Message.__init__(self)
        self.code = code
        if phrase == None:
            phrase = statusCodes[code]
        self.phrase = phrase

    def __repr__(self):
        return "<Response code={code!r}>".format(code=self.code)

    def _getHeaderLine(self):
        return "SIP/2.0 %s %s" % (self.code, self.phrase)

class MessagesParser(LineReceiver):
    """A SIP messages parser.

    Expects dataReceived, dataDone repeatedly,
    in that order. Shouldn't be connected to actual transport.
    """

    version = "SIP/2.0"
    acceptResponses = 1
    acceptRequests = 1
    state = "firstline" # or "headers", "body" or "invalid"

    debug = 0

    def __init__(self, messageReceivedCallback):
        LineReceiver.__init__(self)
        #
        self.__log = logging.getLogger('twirl.protocols.sip')
        #
        self.messageReceived = messageReceivedCallback
        self.reset()

    def reset(self, remainingData=""):
        self.state = "firstline"
        self.length = None # body length
        self.bodyReceived = 0 # how much of the body we received
        self.message = None
        self.header = None
        self.setLineMode(remainingData)

    def invalidMessage(self):
        self.state = "invalid"
        self.setRawMode()

    def dataDone(self):
        # clear out any buffered data that may be hanging around
        self.clearLineBuffer()
        if self.state == "firstline":
            return
        if self.state != "body":
            self.reset()
            return
        if self.length == None:
            # no content-length header, so end of data signals message done
            self.messageDone()
        elif self.length < self.bodyReceived:
            # aborted in the middle
            self.reset()
        else:
            # we have enough data and message wasn't finished? something is wrong
            raise RuntimeError, "this should never happen"

    def dataReceived(self, data):
        try:
            LineReceiver.dataReceived(self, data)
        except Exception as err:
            self.__log.exception(err)
            self.invalidMessage()

    def handleFirstLine(self, line):
        """Expected to create self.message."""
        raise NotImplementedError

    def lineLengthExceeded(self, line):
        self.invalidMessage()

    def lineReceived(self, line):
        if self.state == "firstline":
            while line.startswith("\n") or line.startswith("\r"):
                line = line[1:]
            if not line:
                return
            try:
                a, b, c = line.split(" ", 2)
            except ValueError:
                self.invalidMessage()
                return
            if a == "SIP/2.0" and self.acceptResponses:
                # response
                try:
                    code = int(b)
                except ValueError:
                    self.invalidMessage()
                    return
                self.message = Response(code, c)
            elif c == "SIP/2.0" and self.acceptRequests:
                self.message = Request(a, b)
            else:
                self.invalidMessage()
                return
            self.state = "headers"
            return
        else:
            assert self.state == "headers"
        if line:
            # multiline header
            if line.startswith(" ") or line.startswith("\t"):
                name, value = self.header
                self.header = name, (value + line.lstrip())
            else:
                # new header
                if self.header:
                    self.message.addHeader(*self.header)
                    self.header = None
                try:
                    name, value = line.split(":", 1)
                except ValueError:
                    self.invalidMessage()
                    return
                self.header = name, value.lstrip()
                # XXX we assume content-length won't be multiline
                if name.lower() == "content-length":
                    try:
                        self.length = int(value.lstrip())
                    except ValueError:
                        self.invalidMessage()
                        return
        else:
            # CRLF, we now have message body until self.length bytes,
            # or if no length was given, until there is no more data
            # from the connection sending us data.
            self.state = "body"
            if self.header:
                self.message.addHeader(*self.header)
                self.header = None
            if self.length == 0:
                self.messageDone()
                return
            self.setRawMode()

    def messageDone(self, remainingData=""):
        assert self.state == "body"
        self.message.creationFinished()
        self.messageReceived(self.message)
        self.reset(remainingData)

    def rawDataReceived(self, data):
        assert self.state in ("body", "invalid")
        if self.state == "invalid":
            return
        if self.length == None:
            self.message.bodyDataReceived(data)
        else:
            dataLen = len(data)
            expectedLen = self.length - self.bodyReceived
            if dataLen > expectedLen:
                self.message.bodyDataReceived(data[:expectedLen])
                self.messageDone(data[expectedLen:])
                return
            else:
                self.bodyReceived += dataLen
                self.message.bodyDataReceived(data)
                if self.bodyReceived == self.length:
                    self.messageDone()



class SIPProtocol(DatagramProtocol):
    """ SIPProtocol class for SIP clients and servers.
    """

    def __init__(self, port=PORT, debug=True):
        self.__log = logging.getLogger('twirl.protocols.sip')
        #
        self.port = port
        self.debug = debug
        self.messages = []
        self.parser = MessagesParser(self.addMessage)

    def addMessage(self, msg):
        self.messages.append(msg)

    def datagramReceived(self, data, addr):
        self.parser.dataReceived(data)
        self.parser.dataDone()
        for m in self.messages:
            self._fixupNAT(m, addr)
            if self.debug is True:
                self.__log.debug("Received {m!r} from {addr!r}".format(m=m.toString(), addr=addr))
            if isinstance(m, Request):
                self.handle_request(m, addr)
            else:
                self.handle_response(m, addr)
        self.messages[:] = []

    def _fixupNAT(self, message, (srcHost, srcPort)):
        # RFC 2543 6.40.2,
        senderVia = parseViaHeader(message.headers["via"][0])
        if senderVia.host != srcHost:
            senderVia.received = srcHost
            if senderVia.port != srcPort:
                senderVia.rport = srcPort
            message.headers["via"][0] = senderVia.toString()
        elif senderVia.rport == True:
            senderVia.received = srcHost
            senderVia.rport = srcPort
            message.headers["via"][0] = senderVia.toString()

    def deliverResponse(self, responseMessage):
        """Deliver response.

        Destination is based on topmost Via header."""
        destVia = parseViaHeader(responseMessage.headers["via"][0])
        # XXX we don't do multicast yet
        host = destVia.received or destVia.host
        port = destVia.rport or destVia.port or self.port
        destAddr = URL(host=host, port=port)
        self.sendMessage(destAddr, responseMessage)

    def responseFromRequest(self, code, request):
        """Create a response to a request message."""
        response = Response(code)
        for name in ("via", "to", "from", "call-id", "cseq"):
            response.headers[name] = request.headers.get(name, [])[:]

        return response

    def sendMessage(self, destURL, message):
        """Send a message.

        @param destURL: C{URL}. This should be a *physical* URL, not a logical one.
        @param message: The message to send.
        """
        if destURL.transport not in ("udp", None):
            raise RuntimeError, "only UDP currently supported"
        if self.debug:
            log.msg("Sending %r to %r" % (message.toString(), destURL))
        self.transport.write(message.toString(), (destURL.host, destURL.port or self.PORT))

    def handle_request(self, message, addr):
        """Override to define behavior for requests received

        @type message: C{Message}
        @type addr: C{tuple}
        """
        raise NotImplementedError()

    def handle_response(self, message, addr):
        """Override to define behavior for responses received.

        @type message: C{Message}
        @type addr: C{tuple}
        """
        raise NotImplementedError()
