from multiprocessing import Process
import load_balancer
import user_registry
import config
import chat_server
import time


if __name__ == "__main__":
    """ Dispatches servers in correct order, as processes
    """
    user_registry_process = Process(target=user_registry.main)
    user_registry_process.start()
    load_balancer_process = Process(target=load_balancer.main)
    load_balancer_process.start()
    time.sleep(1)  # Simple solution for avoiding race conditions towards Pyro name server
    for port in config.CHAT_SERVER_PORT_LIST:
        chat_server_process = Process(target=chat_server.main, args=(port, ))
        chat_server_process.start()

