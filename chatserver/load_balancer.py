import sys
import config
sys.path.insert(0, config.LIBRARY_ABSOLUTE_PATH)
import tornado.web
import pyrocomm
import threading
import Pyro4


class LoadBalancer(object):
    def __init__(self):
        self.serverList = []
        self.serverListLock = threading.Lock()

    def get_next_server_address(self):
        """ Returns the next chat server address using round robin scheduling
        """
        with self.serverListLock:
            server = self.serverList.pop()
            self.serverList.insert(0, server)
            httpPort, messageRouterUri = server
            return 'http://localhost' + ':' + str(httpPort)

    def register_chat_server(self, httpPort, messageRouterPyroUri):
        """ Rpc intended for chat servers to register themselves at the load balancer.
        Returns the current registered message routers, including provided router
        """
        with self.serverListLock:
            self.serverList.append((httpPort, messageRouterPyroUri))
            messageRouters = [server[1] for server in self.serverList]
            print('returning: ' + str(messageRouters))
            for routerUri in messageRouters:
                routerProxy = Pyro4.Proxy(routerUri)
                routerProxy.load_balancer_message_routers_notification(messageRouters)

            print('SERVERS');
            print(self.serverList)


global_load_balancer = None


class MainHttpHandler(tornado.web.RequestHandler):
    """ Redirects clients to server provided by load balancer
    """
    def get(self):
        server = global_load_balancer.get_next_server_address()
        self.redirect(server)


def main():
    global global_load_balancer
    global_load_balancer = LoadBalancer()
    daemon, uri = pyrocomm.wrap(global_load_balancer, 'load_balancer', True)
    application = tornado.web.Application([
        (r"/", MainHttpHandler),
        ])
    application.listen(config.LOAD_BALANCER_PORT)
    print('load balancer running')
    tornado.ioloop.IOLoop.instance().start()  # Blocks
