import sys
import config
from threading import Thread
sys.path.insert(0, config.LIBRARY_ABSOLUTE_PATH)
from mailbox import Mailbox
import queue
from protocol import MessageType


class UserRegistry(Thread):
    """ Global registry for user date. Assumed to be running at all times.
     TODO: store and fetch data about users. Add recovery mechanism if user registry crashes
    """
    def __init__(self, mailbox, mailboxTimeoutSec):
        super().__init__()
        self.userToRouterMailboxUri = {}  # Mailbox uri currently not used
        self.mailbox = mailbox
        self.mailboxTimeoutSec = mailboxTimeoutSec
        self.running = True

    def register_new_user(self, userName, messageRouterMailboxUri):
        if userName in self.userToRouterMailboxUri:
            return False
        else:
            self.userToRouterMailboxUri[userName] = messageRouterMailboxUri
            return True

    def remove_user(self, userName):
        if userName in self.userToRouterMailboxUri:
            del self.userToRouterMailboxUri[userName]
            return True
        else:
            return False

    def stop(self):
        self.running = False

    def run(self):
        while self.running:
            try:
                msg = self.mailbox.get(timeout=self.mailboxTimeoutSec)
                userName = msg.data
                mailboxProxy = self.mailbox.get_mailbox_proxy(msg.senderMailboxUri)
                if msg.messageType == MessageType.REGISTER_NEW_USER:
                    isSuccess = self.register_new_user(userName, msg.senderMailboxUri)
                    responseMsg = self.mailbox.create_message(MessageType.REGISTER_NEW_USER, (userName, isSuccess))
                    mailboxProxy.put(responseMsg)
                elif msg.messageType == MessageType.REMOVE_EXISTING_USER:
                    isSuccess = self.remove_user(userName)
                    responseMsg = self.mailbox.create_message(MessageType.REMOVE_EXISTING_USER, (userName, isSuccess))
                    mailboxProxy.put(responseMsg)
            except queue.Empty:
                pass


def main():
    user_registry = UserRegistry(Mailbox.create_mailbox('user_registry'), 1)
    user_registry.start()
    user_registry.join()


if __name__ == "__main__":
    main()
