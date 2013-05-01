import os
import sys
sys.path.insert(0, os.getcwd() + os.sep + os.pardir + os.sep + 'lib')
sys.path.insert(0, os.getcwd() + os.sep + os.pardir + os.sep + 'chatserver')
import unittest
from user_registry import UserRegistry
import mailbox
from protocol import MessageType
import queue


class MailboxMock(mailbox.Mailbox):
    def __init__(self, proxyMock=None):
        super().__init__()
        self.proxyMock = proxyMock

    def get_mailbox_proxy(self, nameOrUri):
        return self.proxyMock


class TestUserRegistry(unittest.TestCase):
    """ Tests user registry by setting up the registry and sending messages.
    Alternatively, methods of registry could be tested separately.
    """
    def setUp(self):
        self.senderMailboxMock = MailboxMock()
        self.userRegistryMailbox = MailboxMock(proxyMock=self.senderMailboxMock)
        self.userRegistry = UserRegistry(self.userRegistryMailbox, 0.01)
        self.userRegistry.start()

    def tearDown(self):
        self.userRegistry.stop()
        self.userRegistry.join()

    def test_register_user(self):
        testUserName = 'test_user_name'
        try:
            # Should register new user correctly
            requestMsg = self.userRegistryMailbox.create_message(MessageType.USER_REGISTRY_NEW_USER, testUserName)
            self.userRegistryMailbox.put(requestMsg)
            responseMsg = self.senderMailboxMock.get(timeout=1)
            self.assertEqual(MessageType.USER_REGISTRY_NEW_USER, responseMsg.messageType)
            userName, isSuccess = responseMsg.data
            self.assertEqual(testUserName, userName)
            self.assertTrue(isSuccess)

            # Should not register same user twice
            self.userRegistryMailbox.put(requestMsg)
            responseMsg = self.senderMailboxMock.get(timeout=1)
            self.assertEqual(MessageType.USER_REGISTRY_NEW_USER, responseMsg.messageType)
            userName, isSuccess = responseMsg.data
            self.assertEqual(testUserName, userName)
            self.assertFalse(isSuccess)
        except queue.Empty:
            self.fail('user registry did not respond in time')


if __name__ == '__main__':
    unittest.main()
