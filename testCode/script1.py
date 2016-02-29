import os
from libmproxy import controller, proxy
from libmproxy.proxy.server import ProxyServer

class StickyMaster(controller.Master):
    def __init__(self,server):
        controller.Master.__init__(self,server)

    def run(self):
        try:
            return controller.Master.run(self)
        except KeyboardInterrupt:
            self.shutdown()

    def handle_request(self,flow):
        

