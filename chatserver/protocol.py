import json


class MessageType:
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

    REGISTER_CHAT_SERVER = 'register_chat_server'
    NEW_MESSAGE_ROUTER = 'new_message_router'
    REGISTER_NEW_USER = 'register_new_user'
    FORWARD_MESSAGE_TO_ALL_CLIENTS = 'forward_message_to_all_clients'


class Message:
    def __init__(self, messsageType):
        self.messageType = messsageType  # Mandatory field for all messages


class ClientMessage(Message):
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
    def __init__(self, messageType, senderMailboxUri, data):
        super().__init__(messageType)
        self.messageType = messageType
        self.senderMailboxUri = senderMailboxUri
        self.data = data
