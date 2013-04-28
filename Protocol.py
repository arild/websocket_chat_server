import json


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


class Message:
    def __init__(self, messageType, senderUserName='', messageText='', receiverUserName='', allUsers=[]):
        self.messageType = messageType  # Mandatory field
        self.senderUserName = senderUserName
        self.messageText = messageText
        self.receiverUserName = receiverUserName  # Only used for private messages
        self.allUsers = allUsers  # Only used for listing of all users


def to_json(message):
    return json.dumps(message.__dict__)


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

    return Message(messageType, senderUserName, messageText, receiverUserName, listAllUsers)