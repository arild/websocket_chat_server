from threading import Thread
import os
import Pyro4.core
import Pyro4.naming


def wrap(target_obj, name=None, daemonize=True):
    """Wraps a standard Python object into a Pyro daemon that accepts remote method calls.

    Might also register the object in a name server
    and/or daemonize the pyro object as a thread
    """
    try:
        daemon = Pyro4.Daemon()
        uri = daemon.register(target_obj)  # register object as a Pyro object
        if name:
            ns = Pyro4.locateNS()
            try:
                ns.unregister(name)
            except Exception:
                pass
            ns.register(name, uri)
        if daemonize:
            thread = Thread(target=daemon.requestLoop, args=())
            thread.start()
        return uri, daemon
    except Exception as e:
        print('failed wrapping to pyro object:' + str(e))
        os._exit(0)