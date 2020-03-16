import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from string import Template

from cloner_service.LoggerFactory import LoggerFactory


class DefaultHTTPRequestHandler(SimpleHTTPRequestHandler):
    def send_headers(self, parameters):
        assert type(parameters) == dict

        for key, value in parameters.items():
            self.send_header(key, value)

        self.end_headers()

    def send_content(self, content):
        self.wfile.write(content)

    def send_error_404(self):
        error_msg = "Not Found resources under %s path" % self.path
        self.send_error(404, error_msg)

    def send_error_500(self, e):
        error_msg = "Couldn't handle request for path: %s - %s" % (self.path, e)
        self.send_error(500, error_msg)

    def get_content_from_template(self, filename, parameters):
        assert type(parameters) == dict

        try:
            with open(filename) as template_file:
                template = Template(template_file.read())
                return template.safe_substitute(parameters)
        except IOError as e:
            raise Exception("Not found template: %s" % filename, e)
        except Exception as e:
            raise Exception("Couldn't get content based on template: %s" % filename, e)

    def get_content_from_file(self, filename):
        try:
            with open(filename) as f:
                return f.read()
        except IOError as e:
            raise Exception("Not found file: %s" % filename, e)
        except Exception as e:
            raise Exception("Couldn't get content based on file: %s" % filename, e)


class HTTPHandler3(DefaultHTTPRequestHandler):
    """python 3"""

    access_logs_logger = LoggerFactory.create_logger("file", "access_logs_logger.conf")

    def log_request(self, code='-', size='-'):
        self.access_logs_logger.info(
            "%s %s %s %s %s",
            self.address_string(),
            self.log_date_time_string(),
            self.requestline,
            str(code),
            str(size))

    def do_GET(self):
        try:
            if self.path == "/":
                self.send_response(200)
                self.send_headers({"Content-type": "text/html; charset=utf-8"})

                # content = self.get_content_from_template("index.html", dict(message="Hello"))
                content = "OK"

                self.send_content(content)
                return

            if self.path == "/content/text":
                self.send_response(200)
                self.send_headers({"Content-type": "text/plain; charset=utf-8"})

                content = self.get_content_from_file("responses/content.txt")

                self.send_content(content)
                return

            if self.path == "/content/html":
                self.send_response(499)
                self.send_headers({"Content-type": "text/html; charset=utf-8"})

                content = self.get_content_from_file("responses/content.html")

                self.send_content(content)
                return

            if self.path == "/content/json":
                self.send_response(200)
                self.send_headers({"Content-type": "application/json; charset=utf-8"})

                content = self.get_content_from_file("responses/content.json")

                self.send_content(content)
                return

        except Exception as e:
            self.send_error_500(e)
            return

        self.send_error_404()
        return

    def send_content(self, content):
        if str == type(content):
            self.wfile.write(bytes(content, "utf8"))
        else:
            self.wfile.write(bytes(content.read(), "utf8"))


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True

    def shutdown(self):
        self.socket.close()
        HTTPServer.shutdown(self)


class SimpleHttpServer:
    def __init__(self, ip, port):
        self.LOGGER = LoggerFactory.create_logger(self.__class__.__name__, "webserver_logger.conf")

        self.LOGGER.info("init")
        self.server = ThreadedHTTPServer((ip, port), HTTPHandler3)
        self.server_thread = None

    def start(self):
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def wait_for_thread(self):
        self.server_thread.join()

    def stop(self):
        self.server.shutdown()
        self.wait_for_thread()


if __name__ == '__main__':
    server = SimpleHttpServer('127.0.0.1', 8080)
    try:
        print('HTTP Server Running...........')
        server.start()
        server.wait_for_thread()
    except KeyboardInterrupt:
        server.stop()
        pass
