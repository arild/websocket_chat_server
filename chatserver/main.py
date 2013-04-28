import lib.tornado.web


class MainHttpHandler(lib.tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

application = lib.tornado.web.Application([
    (r"/", MainHttpHandler),
])

if __name__ == "__main__":
    application.listen(8888)
    lib.tornado.ioloop.IOLoop.instance().start()