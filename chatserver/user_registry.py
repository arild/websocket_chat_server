import sys
import config

sys.path.insert(0, config.LIBRARY_ABSOLUTE_PATH)
import threading
import mailbox
from protocol import MessageType


class UserRegistry(object):
    def __init__(self):
        self.users = {}
        self.usersLock = threading.Lock()
        self.mailbox = mailbox.create_mailbox('user_registry')

    def register_new_user(self, userName, messageRouterMailboxUri):
        if userName in self.users:
            return False
        else:
            self.users[userName] = messageRouterMailboxUri
            return True

    def run_forever(self):
        while True:
            msg = self.mailbox.get()
            if msg.messageType == MessageType.REGISTER_NEW_USER:
                userName = msg.data
                isSuccess = self.register_new_user(userName, msg.senderMailboxUri)
                proxy = mailbox.get_mailbox_proxy(msg.senderMailboxUri)
                responseMsg = self.mailbox.create_message(MessageType.REGISTER_NEW_USER, (userName, isSuccess))
                proxy.put(responseMsg)


def main():
    user_registry = UserRegistry()
    user_registry.run_forever()


if __name__ == "__main__":
    main()
