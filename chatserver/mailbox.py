import queue
import pyrocomm
import Pyro4
from protocol import ServerMessage


class Mailbox(queue.Queue):
    """ A thread-safe mailbox abstraction that is intended to be wrapped
    as a remote object
    """
    def __init__(self):
        super().__init__(100)
        self.uri = None
        self.daemon = None

    def create_message(self, messageType, data):
        """ Wraps creation of server messages, and adds this mailbox's uri to the message
        """
        return ServerMessage(messageType, self.uri, data)


def create_mailbox(name=None):
    """ Factory for mailbox class. Wraps the mailbox into a remote object.
    """
    mailbox = Mailbox()
    mailbox.uri, mailbox.daemon = pyrocomm.wrap(mailbox, name, daemonize=True)
    return mailbox


def get_mailbox_proxy(nameOrUri):
    """ Returns a proxy for a mailbox identificator.
    Look up a mailbox in global naming registry if a name is provided.
    If a uri is provided, the naming registry is not accessed
    """
    if isinstance(nameOrUri, str):
        return Pyro4.Proxy('PYRONAME:' + nameOrUri)
    else:
        return Pyro4.Proxy(nameOrUri)