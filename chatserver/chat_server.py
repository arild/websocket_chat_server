import os
import sys
import config
sys.path.insert(0, config.LIBRARY_ABSOLUTE_PATH)
import Protocol
import tornado.web
import tornado.websocket
import pyrocomm
import Pyro4


class MessageRouter():
    """ Remote object routing messages and handling other user activity, such as login
    """
    def __init__(self, httpPort):
        self.httpPort = httpPort
        self.uri = None
        self.load_balancer = None
        self.users = {}
        self.messageHandlers = {
            Protocol.LOGIN: self.login_handler,
            Protocol.LOGOUT: self.logout_handler,
            Protocol.PUBLIC_MESSAGE: self.public_message_handler,
            Protocol.PRIVATE_MESSAGE: self.private_message_handler,
            Protocol.LIST_ALL_USERS: self.list_all_users_handler
        }

    def set_message_router_uri(self, uri):
        self.uri = uri

    def notify_load_balancer(self):
        """ Registers message router at load balancer
        """
        self.load_balancer = Pyro4.Proxy('PYRONAME:load_balancer')  # name server object lookup uri shortcut
        self.load_balancer.register_chat_server(self.httpPort, self.uri)

    def handle_message(self, msg, senderConnection):
        """ Invokes handler for message type
        """
        if msg.messageType in self.messageHandlers:
            self.messageHandlers[msg.messageType](msg, senderConnection)
        else:
            pass  # Discard message

    def login_handler(self, msg, senderConnection):
        if msg.senderUserName in self.users:
            newMsg = Protocol.Message(Protocol.LOGIN_FAILED, messageText='user name already taken')
            senderConnection.send_message(newMsg)
        else:
            self.users[msg.senderUserName] = senderConnection
            for userName, senderConnection in self.users.items():
                senderConnection.send_message(msg)

    def logout_handler(self, msg, senderConnection):
        del self.users[msg.senderUserName]

    def public_message_handler(self, msg, senderConnection):
        for userName, connection in self.users.items():
            connection.send_message(msg)

    def private_message_handler(self, msg, senderConnection):
        """ Sends a private message to specified and requesting user
        If user does not exist, message is dropped
        """
        if msg.receiverUserName in self.users:
            receiverConnection = self.users[msg.receiverUserName]
            receiverConnection.send_message(msg)
            senderConnection.send_message(msg)
        else:
            print('user does not exist: ' + msg.senderUserName)

    def list_all_users_handler(self, msg, senderConnection):
        newMsg = Protocol.Message(Protocol.LIST_ALL_USERS, allUsers=list(self.users.keys()))
        senderConnection.send_message(newMsg)


global_message_router = None


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    """ Accepts web socket connections
    """
    def on_message(self, message):
        """ Wraps de-serialization of message object
        """
        print('received:')
        print(message)
        msg = Protocol.from_json(message)
        global_message_router.handle_message(msg, self)

    def send_message(self, message):
        """ Wraps serialization of message object
        """
        print('sending:')
        print(Protocol.to_json(message))
        self.write_message(Protocol.to_json(message))


class MainHandler(tornado.web.RequestHandler):
    """ Serves static media over http. Invoked once by each client to load page.
    """
    def get(self):
        self.render('index.html')

    def set_extra_headers(self, path):
        self.set_header("Cache-control", "no-cache")


def main(httpPort):
    global global_message_router
    global_message_router = MessageRouter(httpPort)
    daemon, uri = pyrocomm.wrap(global_message_router)
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
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main(8080)