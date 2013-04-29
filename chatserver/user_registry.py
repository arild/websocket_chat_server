import sys
import config
sys.path.insert(0, config.LIBRARY_ABSOLUTE_PATH)
import pyrocomm
import threading
import Pyro4


class UserRegistry(object):
    def __init__(self):
        self.users = {}
        self.usersLock = threading.Lock()

    def register_new_user(self, userName, messageRouterPyroUri):
        print('CURRENT USERS: ')
        print(self.users)
        with self.usersLock:
            if userName in self.users:
                self.users[userName] = messageRouterPyroUri
                return True
            else:
                return False

    def hello(self):
        print('** hello')
        return '**hello'


global_user_registry = None


def main():
    global global_user_registry
    global_user_registry = UserRegistry()
    daemon, uri = pyrocomm.wrap(global_user_registry, 'user_registry', False)
    daemon.requestLoop()


if __name__ == "__main__":
    main()
