websocket_chat_server
=====================

Simple distributed chat server using WebSockets with a Web interface.
Distributed in the sense that server instances run locally as processes communicating over localhost. Tested with Python 3.2 and 3.3.

External libraries included in repository:
- Pyro4 (remote objects)
- Tornaodo (Web and WebSocket server)

Chat server requires a Pyro4 naming server running:
- cd lib
- python -m Pyro4.naming (or python -m Pyro4.naming -n \<host address\> if name server binds to localhost)

Start chat server with:
- cd chatserver
- python startup.py
- Go to http://localhost:8000 (where load balancer will redirect)

Run test:
- cd test
- python -m unittest test_user_registry.py




