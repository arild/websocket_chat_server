import tornado.ioloop
import tornado.web
import tornado.websocket
import os
import Protocol


class MessageRouter():
    def __init__(self):
        self.users = {}
        self.message_handlers = {
            Protocol.LOGIN: self.login_handler,
            Protocol.LOGOUT: self.logout_handler,
            Protocol.PUBLIC_MESSAGE: self.public_message_handler,
            Protocol.PRIVATE_MESSAGE: self.private_message_handler,
            Protocol.LIST_ALL_USERS: self.list_all_users_handler
        }

    def handle_message(self, msg, senderConnection):
        """ Invokes handler for message type
        """
        self.message_handlers[msg.messageType](msg, senderConnection)

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


global_message_router = MessageRouter()


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        pass

    def on_message(self, message):
        """ Wraps de-serialization of message object
        """
        print('received:')
        print(message)
        msg = Protocol.from_json(message)
        global_message_router.handle_message(msg, self)

    def on_close(self):
        print("WebSocket closed")

    def send_message(self, message):
        """ Wraps serialization of message object
        """
        print('sending:')
        print(Protocol.to_json(message))
        self.write_message(Protocol.to_json(message))


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')

    def set_extra_headers(self, path):
        self.set_header("Cache-control", "no-cache")


if __name__ == "__main__":
    application = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/websocket", WebSocketHandler)
        ],
        template_path = os.path.join(os.path.dirname(__file__), "templates"),
        static_path = os.path.join(os.path.dirname(__file__), "static")
    )
    application.listen(8080)
    tornado.ioloop.IOLoop.instance().start()