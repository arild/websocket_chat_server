import os
import sys
import config
sys.path.insert(0, config.LIBRARY_ABSOLUTE_PATH)
import protocol
import queue
import tornado.web
import tornado.websocket
import pyrocomm
import Pyro4
from threading import Thread


class MessageRouter(Thread):
    """ Remote object routing messages and handling other user activity, such as login
    """
    def __init__(self, httpPort):
        self.messageBox = queue.Queue()
        self.httpPort = httpPort
        self.routerUri = None
        self.loadBalancerProxy = Pyro4.Proxy('PYRONAME:load_balancer')  # name server object lookup uri shortcut
        self.userRegistryProxy = Pyro4.Proxy('PYRONAME:user_registry')  # name server object lookup uri shortcut
        self.messageRouterUris = []  # Contains all message routers in system
        self.userToRouter = {}
        self.userToWebSocketConnection = {}
        self.routerToUsers = {}
        self.messageHandlers = {
            protocol.LOGIN: self.login_handler,
            protocol.LOGOUT: self.logout_handler,
            protocol.PUBLIC_MESSAGE: self.public_message_handler,
            protocol.PRIVATE_MESSAGE: self.private_message_handler,
            protocol.LIST_ALL_USERS: self.list_all_users_handler
        }

    def set_message_router_uri(self, uri):
        self.routerUri = uri

    def notify_load_balancer(self):
        """ Registers message router at load balancer
        """
        self.loadBalancerProxy.register_chat_server(self.httpPort, self.routerUri)

    def handle_message(self, msg, senderConnection):
        """ Invokes handler for message type
        """
        if msg.messageType in self.messageHandlers:
            self.messageHandlers[msg.messageType](msg, senderConnection)
        else:
            pass  # Discard message

    def login_handler(self, msg, senderConnection):
        userNameAlreadyTaken = self.userRegistryProxy.register_new_user(msg.senderUserName, self.routerUri)
        if userNameAlreadyTaken:
            newMsg = protocol.Message(protocol.LOGIN_FAILED, messageText='user name already taken')
            senderConnection.send_message(newMsg)
        else:
            self.userToWebSocketConnection[msg.senderUserName] = senderConnection  # Connection stored locally
            print('******** login handler')
            print(self.messageRouterUris)
            for uri in self.messageRouterUris:  # Broadcast successful login, conceptually to current router too
                Pyro4.Proxy(uri).login_success(self.routerUri, msg)

    def logout_handler(self, msg, senderConnection):
        del self.userToRouter[msg.senderUserName]

    def public_message_handler(self, msg, senderConnection):
        for userName, connection in self.userToRouter.items():
            connection.send_message(msg)

    def private_message_handler(self, msg, senderConnection):
        """ Sends a private message to specified and requesting user
        If user does not exist, message is dropped
        """
        if msg.receiverUserName in self.userToRouter:
            receiverConnection = self.userToRouter[msg.receiverUserName]
            receiverConnection.send_message(msg)
            senderConnection.send_message(msg)
        else:
            print('user does not exist: ' + msg.senderUserName)

    def list_all_users_handler(self, msg, senderConnection):
        newMsg = protocol.Message(protocol.LIST_ALL_USERS, allUsers=list(self.userToRouter.keys()))
        senderConnection.send_message(newMsg)

    def load_balancer_message_routers_notification(self, messageRouters):
        self.messageRouterUris = messageRouters

    def login_success(self, routerUriHostingUser, loginMsg):
        print('login success')
        self.userToRouter[loginMsg.senderUserName] = routerUriHostingUser
        if routerUriHostingUser in self.routerToUsers:
            self.routerToUsers[routerUriHostingUser].append(loginMsg.senderUserName)
        else:
            self.routerToUsers[routerUriHostingUser] = [loginMsg.senderUserName]
        print('done book keeping')
        for userName, connection in self.userToWebSocketConnection.items():
            connection.send_message(loginMsg)

    def run(self):
        pass


global_message_router = None


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *request, **kwargs):
        super().__init__(request[0], request[1])

    """ Accepts web socket connections
    """
    def on_message(self, message):
        """ Wraps de-serialization of message object
        """
        print('received:')
        print(message)
        msg = protocol.from_json(message)
        global_message_router.handle_message(msg, self)

    def send_message(self, message):
        """ Wraps serialization of message object
        """
        print('sending:')
        print(protocol.to_json(message))
        self.write_message(protocol.to_json(message))


class MainHandler(tornado.web.RequestHandler):
    def __init__(self, *request, **kwargs):
        super().__init__(request[0], request[1])

    """ Serves static media over http. Invoked once by each client to load page.
    """
    def get(self):
        self.render('index.html')

    def set_extra_headers(self, path):
        self.set_header("Cache-control", "no-cache")


def main(httpPort):
    global global_message_router
    global_message_router = MessageRouter(httpPort)
    daemon, uri = pyrocomm.wrap(global_message_router, daemonize=True)
    global_message_router.set_message_router_uri(uri)
    global_message_router.notify_load_balancer()

    application = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/websocket", WebSocketHandler)
        ],
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static")
    )
    application.listen(httpPort)
    print('chat server running on port ' + str(httpPort))
    tornado.ioloop.IOLoop.instance().start()  # Blocks


if __name__ == "__main__":
    main(8080)