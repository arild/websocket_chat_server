import os
import sys
import config
sys.path.insert(0, config.LIBRARY_ABSOLUTE_PATH)
import tornado.web
import tornado.websocket
from mailbox import Mailbox
from threading import Thread
from protocol import ClientMessage, MessageType


class MessageRouter(Thread):
    """ Routes messages between servers and clients.

    Based on actor pattern, that is, sequential processing of messages
    which removes the need for mutual exclusion primitives.

    A message router hosts arbitrary many client connections, and has knowledge
    about all other message router in the system.
    """
    def __init__(self, httpPort):
        super().__init__()
        self.mailbox = Mailbox.create_mailbox()
        self.messageRouterMailboxes = []  # Contains all message routers in system
        self.userToRouterMailbox = {}  # Maps a user name to residing message router. Used for private messages
        self.userToWebSocketConnection = {}  # Holds local web sockets connections
        self.pendingUserLoginToWebSocketConnection = {}  # Holds connections for users that are requesting login at user registry
        self.clientMessageHandlers = {
            MessageType.LOGIN: self.login_handler,
            MessageType.LOGOUT: self.logout_handler,
            MessageType.PUBLIC_MESSAGE: self.public_message_handler,
            MessageType.PRIVATE_MESSAGE: self.private_message_handler,
            MessageType.LIST_ALL_USERS: self.list_all_users_handler
        }
        self.serverMessageHandlers = {
            MessageType.USER_REGISTRY_NEW_USER: self.user_registry_new_user_handler,
            MessageType.USER_REGISTRY_REMOVE_USER: self.user_registry_remove_user_handler,
            MessageType.NEW_USER: self.new_user_handler,
            MessageType.REMOVE_USER: self.remove_user_handler,
            MessageType.NEW_MESSAGE_ROUTER: self.new_message_router_handler,
            MessageType.FORWARD_PUBLIC_MESSAGE_TO_ALL_CLIENTS: self.forward_public_message_to_all_clients_handler,
            MessageType.FORWARD_PRIVATE_MESSAGE_TO_CLIENT: self.forward_private_message_to_client
        }

        self.userRegistryMailbox = self.mailbox.get_mailbox_proxy('user_registry')
        self.loadBalancerMailbox = self.mailbox.get_mailbox_proxy('load_balancer')

        # Notify load balancer about this message router
        msg = self.mailbox.create_message(MessageType.REGISTER_CHAT_SERVER, httpPort)
        self.loadBalancerMailbox.put(msg)

    def handle_client_message(self, msg, senderConnection):
        """ Invokes handler for client message type
        """
        if msg.messageType in self.clientMessageHandlers:
            print('handling client message: ' + msg.messageType)
            self.clientMessageHandlers[msg.messageType](msg, senderConnection)
        else:
            print('unknown client message: ' + msg.messageType)  # Discard message

    def handle_server_message(self, msg):
        """ Invokes handler for server message type
        """
        if msg.messageType in self.serverMessageHandlers:
            print('handling server message: ' + msg.messageType)
            self.serverMessageHandlers[msg.messageType](msg)
        else:
            print('unknown server message: ' + msg.messageType)  # Discard message

    ### Client message handlers ###

    def login_handler(self, clientMsg, senderConnection):
        self.pendingUserLoginToWebSocketConnection[clientMsg.senderUserName] = senderConnection  # Connection stored locally
        requestMsg = self.mailbox.create_message(MessageType.USER_REGISTRY_NEW_USER, clientMsg.senderUserName)
        self.userRegistryMailbox.put(requestMsg)

    def logout_handler(self, clientMsg, senderConnection):
        if clientMsg.senderUserName not in self.userToWebSocketConnection:
            print('user should have a connection on logout')  # Log error. Discard message.
        else:
            requestMsg = self.mailbox.create_message(MessageType.USER_REGISTRY_REMOVE_USER, clientMsg.senderUserName)
            self.userRegistryMailbox.put(requestMsg)

    def public_message_handler(self, clientMsg, senderConnection):
        serverMsg = self.mailbox.create_message(MessageType.FORWARD_PUBLIC_MESSAGE_TO_ALL_CLIENTS, clientMsg)
        self._send_to_all_message_routers(serverMsg)

    def private_message_handler(self, clientMsg, senderConnection):
        """ Sends a private message to specified and requesting user
        If user does not exist, message is dropped
        """
        if clientMsg.receiverUserName in self.userToRouterMailbox:
            # Lookup message router hosting client, possibly this instance
            routerMailbox = self.userToRouterMailbox[clientMsg.receiverUserName]
            serverMsg = self.mailbox.create_message(MessageType.FORWARD_PRIVATE_MESSAGE_TO_CLIENT, clientMsg)
            routerMailbox.put(serverMsg)
            senderConnection.send_message(clientMsg)  # Notification to sender
        else:
            # Target user does not exist, discard message
            print('user does not exist: ' + clientMsg.receiverUserName)

    def list_all_users_handler(self, msg, senderConnection):
        newMsg = ClientMessage(MessageType.LIST_ALL_USERS, allUsers=list(self.userToRouterMailbox.keys()))
        senderConnection.send_message(newMsg)

    ### Server message handlers ###

    def user_registry_new_user_handler(self, msg):
        """ Handles response from user registry whether login was successful or not
        """
        userName, successfullyRegistered = msg.data

        # Removed user from temporary storage for waiting for user registry response
        connection = self.pendingUserLoginToWebSocketConnection[userName]
        del self.pendingUserLoginToWebSocketConnection[userName]

        if successfullyRegistered:
            self.userToWebSocketConnection[userName] = connection  # Permanently store connection
            serverMsg = self.mailbox.create_message(MessageType.NEW_USER, userName)
            self._send_to_all_message_routers(serverMsg)
        else:
            newMsg = ClientMessage(MessageType.LOGIN_FAILED, messageText='user name already taken')
            connection.send_message(newMsg)

    def user_registry_remove_user_handler(self, msg):
        userName, successfullyRemoved = msg.data
        if successfullyRemoved:
            serverMsg = self.mailbox.create_message(MessageType.REMOVE_USER, userName)
            self._send_to_all_message_routers(serverMsg)
        else:
            connection = self.userToWebSocketConnection[userName]
            responseMsg = ClientMessage(MessageType.LOGOUT_FAILED, messageText='user does not exist')
            connection.send_message(responseMsg)

    def new_user_handler(self, msg):
        userName = msg.data
        if userName in self.userToRouterMailbox:
            # User should not already be registered. Log error, and discard message. Let client time out and retry.
            print('warning: user should not already be registered')
        else:
            self.userToRouterMailbox[userName] = self.mailbox.get_mailbox_proxy(msg.senderMailboxUri)
            clientMsg = ClientMessage(MessageType.LOGIN, userName)
            self._send_to_all_local_clients(clientMsg)

    def remove_user_handler(self, msg):
        userName = msg.data
        if userName not in self.userToRouterMailbox:
            # Should be registered. Log error, and discard message
            print('warning: user should be registered')
        else:
            clientMsg = ClientMessage(MessageType.LOGOUT, userName)
            self._send_to_all_local_clients(clientMsg)

            if userName in self.userToWebSocketConnection:
                # This instance is hosting the user to be removed
                # Remove book-keeping about client
                del self.userToWebSocketConnection[userName]
                del self.userToRouterMailbox[userName]

    def forward_public_message_to_all_clients_handler(self, msg):
        """ Request from message router to send attached message to all users of this message router
        """
        clientMsg = msg.data
        self._send_to_all_local_clients(clientMsg)

    def forward_private_message_to_client(self, msg):
        clientMsg = msg.data
        if clientMsg.receiverUserName in self.userToWebSocketConnection:
            connection = self.userToWebSocketConnection[clientMsg.receiverUserName]
            connection.send_message(clientMsg)
        else:
            # Routing error. Discard message
            print('can not find connection for private message')

    def new_message_router_handler(self, msg):
        """ Notification from load balancer about message routers.
        """
        self.messageRouterMailboxes = [self.mailbox.get_mailbox_proxy(uri) for uri in msg.data]

    def _send_to_all_message_routers(self, msg):
        """ Helper method for broadcasting to all message routers in system, including current instance
        """
        for routerMailbox in self.messageRouterMailboxes:
            routerMailbox.put(msg)

    def _send_to_all_local_clients(self, msg):
        """ Helper method for broadcasting to all local clients
        """
        for userName, connection in self.userToWebSocketConnection.items():
            connection.send_message(msg)

    def _handle_messages_forever(self):
        def is_client_msg(msg):
            return isinstance(msg, tuple)

        while True:
            msg = self.mailbox.get()  # Blocks
            if is_client_msg(msg):
                # Client message in mailbox is a tuple of the client's message and connection
                msg, connection = msg
                self.handle_client_message(msg, connection)
            else:
                # Server message is just the message
                self.handle_server_message(msg)

    def run(self):
        self._handle_messages_forever()


global_message_router_mailbox = None


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    """ Accepts web socket connections
    """
    def __init__(self, *request, **kwargs):
        super().__init__(request[0], request[1])

    def on_message(self, message):
        """ Wraps de-serialization of message object
        """
        print('received client message:')
        print(message)
        msg = ClientMessage.from_json(message)
        global_message_router_mailbox.put((msg, self))

    def send_message(self, message):
        """ Wraps serialization of message object
        """
        print('sending client message:')
        print(ClientMessage.to_json(message))
        self.write_message(ClientMessage.to_json(message))


class MainHandler(tornado.web.RequestHandler):
    """ Serves static media over http. Invoked once by each client to load page.
    """
    def __init__(self, *request, **kwargs):
        super().__init__(request[0], request[1])

    def get(self):
        self.render('index.html')

    def set_extra_headers(self, path):
        self.set_header("Cache-control", "no-cache")  # For development


def main(httpPort):
    messageRouter = MessageRouter(httpPort)
    global global_message_router_mailbox
    global_message_router_mailbox = messageRouter.mailbox
    messageRouter.start()

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
    main(8001)