import sys
import config
sys.path.insert(0, config.LIBRARY_ABSOLUTE_PATH)
import tornado.web
import threading
from mailbox import Mailbox
from protocol import MessageType


class LoadBalancer(threading.Thread):
    """ Access point for clients. Round robin scheduling of front-end servers.

    TODO: Detect front-end server failure and broadcast notification
    """
    def __init__(self):
        super().__init__()
        self.serverList = []
        self.serverListLock = threading.Lock()
        self.mailbox = Mailbox.create_mailbox('load_balancer')

    def get_next_server_address(self):
        """ Returns the next chat server address using round robin scheduling.
        Thread-safe, can be called externally
        """
        with self.serverListLock:
            server = self.serverList.pop()
            self.serverList.insert(0, server)
            httpPort, messageRouterUri = server
            return 'http://localhost' + ':' + str(httpPort)

    def register_chat_server(self, msg):
        """ Returns the current registered message routers, including provided router
        """
        chatServerHttpPort = msg.data
        with self.serverListLock:
            self.serverList.append((chatServerHttpPort, msg.senderMailboxUri))
            messageRouters = [server[1] for server in self.serverList]
        for routerUri in messageRouters:
            routerMailbox = self.mailbox.get_mailbox_proxy(routerUri)
            msg = self.mailbox.create_message(MessageType.NEW_MESSAGE_ROUTER, messageRouters)
            routerMailbox.put(msg)

    def run(self):
        while True:
            msg = self.mailbox.get()
            if msg.messageType == MessageType.REGISTER_CHAT_SERVER:
                    self.register_chat_server(msg)


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
    global_load_balancer.start()
    application = tornado.web.Application([
        (r"/", MainHttpHandler),
        ])
    application.listen(config.LOAD_BALANCER_PORT)
    print('load balancer running')
    tornado.ioloop.IOLoop.instance().start()  # Blocks
