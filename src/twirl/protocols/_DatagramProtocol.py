class DatagramProtocol(object):
     def connectionRefused(self):
         pass

     def datagramReceived(self, datagram, addr):
         pass

     def doStart(self):
        def recv_cb(udp_handle, (ip, port), flags, data, error):
            self.datagramReceived(data, (ip, port))
        self.transport.start_recv(recv_cb)

     def doStop(self):
         pass
