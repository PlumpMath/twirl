#

class LineReceiver(object):
    def __init__(self):
        self.line_mode = 1
        self._buffer = b''
        self._busyReceiving = False
        self.delimiter = b'\r\n'
        self.MAX_LENGTH = 16384

    def clearLineBuffer(self):
        """
        Clear buffered data.

        @return: All of the cleared buffered data.
        @rtype: C{bytes}
        """
        b, self._buffer = self._buffer, b''
        return b

    def dataReceived(self, data):
        """
        Translates bytes into lines, and calls lineReceived (or
        rawDataReceived, depending on mode.)
        """
        if self._busyReceiving:
            self._buffer += data
            return

        try:
            self._busyReceiving = True
            self._buffer += data
            while self._buffer:
                if self.line_mode:
                    try:
                        line, self._buffer = self._buffer.split(self.delimiter, 1)
                    except ValueError:
                        if len(self._buffer) > self.MAX_LENGTH:
                            line, self._buffer = self._buffer, b''
                            return self.lineLengthExceeded(line)
                        return
                    else:
                        lineLength = len(line)
                        if lineLength > self.MAX_LENGTH:
                            exceeded = line + self.delimiter + self._buffer
                            self._buffer = b''
                            return self.lineLengthExceeded(exceeded)
                        why = self.lineReceived(line)
                        if why:
                            return why
                else:
                    data = self._buffer
                    self._buffer = b''
                    why = self.rawDataReceived(data)
                    if why:
                        return why
        finally:
            self._busyReceiving = False

    def setLineMode(self, extra=b''):
        """
        Sets the line-mode of this receiver.

        If you are calling this from a rawDataReceived callback,
        you can pass in extra unhandled data, and that data will
        be parsed for lines.  Further data received will be sent
        to lineReceived rather than rawDataReceived.

        Do not pass extra data if calling this function from
        within a lineReceived callback.
        """
        self.line_mode = 1
        if extra:
            return self.dataReceived(extra)

    def setRawMode(self):
        """
        Sets the raw mode of this receiver.
        Further data received will be sent to rawDataReceived rather
        than lineReceived.
        """
        self.line_mode = 0

    def rawDataReceived(self, data):
        """
        Override this for when raw data is received.
        """
        raise NotImplementedError()


    def lineReceived(self, line):
        """
        Override this for when each line is received.

        @param line: The line which was received with the delimiter removed.
        @type line: C{bytes}
        """
        raise NotImplementedError()


    def sendLine(self, line):
        """
        Sends a line to the other end of the connection.

        @param line: The line to send, not including the delimiter.
        @type line: C{bytes}
        """
        return self.transport.write(line + self.delimiter)


    def lineLengthExceeded(self, line):
        """
        Called when the maximum line length has been reached.
        Override if it needs to be dealt with in some special way.

        The argument 'line' contains the remainder of the buffer, starting
        with (at least some part) of the line which is too long. This may
        be more than one line, or may be only the initial portion of the
        line.
        """
        return self.transport.loseConnection()
