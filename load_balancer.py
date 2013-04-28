from config import config
import tornado.ioloop
import tornado.web


class LoadBalancer:
    def __init__(self): 
        self.server_list = config['FRONT_END_SERVER_LIST']
        print(self.server_list);
         
    def get_next_server_address(self):
        server = self.server_list.pop()
        self.server_list.insert(0, server)
        return 'http://' + server[0] + ':' + str(server[1])


global_load_balancer = LoadBalancer()


class MainHttpHandler(tornado.web.RequestHandler):
    def get(self):
        server = global_load_balancer.get_next_server_address()
        print(server)
        self.redirect("http://localhost:8080/hello/arild")


if __name__ == "__main__":
    application = tornado.web.Application([
        (r"/", MainHttpHandler),
    ])
    application.listen(9000)
    tornado.ioloop.IOLoop.instance().start()
