import json


class MessageType:
    """ Defines all client and server message types

    TODO: Might add factory method for the different message types for
    making the messages' structure more explicit
    """

    ### Client messages ###

    """ Client request for login.
    Server acknowledgment for successful login.
    Server expects 'senderUserName' field to be set.
    """
    LOGIN = 'login'

    """ Server notification to client regarding failed login.
    Client expects 'messageText' field to contain reason for failure
    """
    LOGIN_FAILED = 'login_failed'

    """ Client request for logout.
    Server acknowledgment for successful logout
    Server expects 'senderUserName' field to be set.
    """
    LOGOUT = 'logout'

    """ Server notification to client regarding failed logout.
    Client expects 'messageText' field to contain reason for failure
    """
    LOGOUT_FAILED = 'logout_failed'

    """ Client request to send message to all users logged in.
    Server notification to client about public message.
    Expects 'senderUserName' and 'messageText' fields to be set.
    """
    PUBLIC_MESSAGE = 'public_message'

    """ Client request to send message to specified user.
    Server notification about private message.
    Expects 'senderUserName', 'messageText' and 'receiverUserName' fields to be set.

    Both 'senderUserName' and 'receiverUserName' should receive server notification.
    """
    PRIVATE_MESSAGE = 'private_message'

    """ Client request for all users currently logged in.
    Server response containing all users logged in.
    Client expects 'allUsers' field to be set.
    """
    LIST_ALL_USERS = 'list_all_users'

    ### Server messages (between chat servers, load balancer and user registry) ###

    """ Request for registering a chat server at the load balancer
    """
    REGISTER_CHAT_SERVER = 'register_chat_server'

    """ Notification between message routers when a new chat server and
    associated message router has been registered successfully
    """
    NEW_MESSAGE_ROUTER = 'new_message_router'

    """ Chat server request for looking up or creating a new user in global user registry.
    User registry response for whether request was successful or not
    """
    USER_REGISTRY_NEW_USER = 'user_registry_new_user'

    """ Chat server request for removing/logging out user in global user registry.
    User registry response for whether request was successful or not
    """
    USER_REGISTRY_REMOVE_USER = 'user_registry_remove_user'

    """ Notification between chat servers about successful user login
    """
    NEW_USER = 'new_user'

    """ Notification between chat servers about successful logout
    """
    REMOVE_USER = 'remove_user'

    """ Request to message router to forward attached message to all clients
    """
    FORWARD_PUBLIC_MESSAGE_TO_ALL_CLIENTS = 'forward_message_to_all_clients'

    """ Request to message router to forward attached message to a specified client
    """
    FORWARD_PRIVATE_MESSAGE_TO_CLIENT = 'forward_message_to_client'


class Message:
    """ Base class for messages. All messages must have a message type.
    """
    def __init__(self, messsageType):
        self.messageType = messsageType  # Mandatory field for all messages


class ClientMessage(Message):
    """ Used between chat server and clients
    """
    def __init__(self, messageType, senderUserName='', messageText='', receiverUserName='', allUsers=[]):
        super().__init__(messageType)
        self.senderUserName = senderUserName
        self.messageText = messageText
        self.receiverUserName = receiverUserName  # Only used for private messages
        self.allUsers = allUsers  # Only used for listing of all users

    @staticmethod
    def to_json(message):
        return json.dumps(message.__dict__)

    @staticmethod
    def from_json(message):
        dict = json.loads(message)
        messageType = dict['messageType']
        senderUserName = dict['senderUserName']
        messageText = ''
        receiverUserName = ''
        listAllUsers = []
        if 'messageText' in dict:
            messageText = dict['messageText']
        if 'receiverUserName' in dict:
            receiverUserName = dict['receiverUserName']
        if 'list_all_users' in dict:
            listAllUsers = dict['receiverUserName']

        return ClientMessage(messageType, senderUserName, messageText, receiverUserName, listAllUsers)


class ServerMessage(Message):
    """ Used between servers, chat servers, load balancer and user registry
    """
    def __init__(self, messageType, senderMailboxUri, data):
        super().__init__(messageType)
        self.messageType = messageType
        self.senderMailboxUri = senderMailboxUri
        self.data = data
