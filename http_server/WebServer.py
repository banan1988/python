import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
from logging import DEBUG, StreamHandler, Formatter
from logging import getLogger
from socketserver import ThreadingMixIn
from string import Template


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass


class WebServer:
    __httpd = None
    __running = True

    def __init__(self, port, server=ThreadingHTTPServer, handler=BaseHTTPRequestHandler):
        self.port = port
        self.server = server
        self.handler = handler
        self.LOGGER = self.__create_console_logger(self.__class__.__name__)

    @staticmethod
    def __create_console_logger(name, level=DEBUG):
        # create logger
        logger = getLogger(name)
        logger.setLevel(level)

        # create console handler and set level to debug
        handler = StreamHandler()
        handler.setLevel(level)

        # create formatter
        formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # add formatter to handler
        handler.setFormatter(formatter)

        # add ch to logger
        logger.addHandler(handler)
        return logger

    def __run_forever(self):
        try:
            self.__httpd = self.server(('', self.port), self.handler)

            self.LOGGER.info("Listening on port: %d", self.port)
            # httpd.serve_forever()
            while self.__running:
                sys.stdout.flush()
                self.__httpd.handle_request()
        except Exception as e:
            self.LOGGER.warn("Couldn't start server on port: %d -  %s", self.port, e)
        finally:
            self.__shutdown()

    def __shutdown(self):
        try:
            self.__httpd.shutdown()
            self.LOGGER.info("Stopped listening on port: %d", self.port)
        except Exception as e:
            self.LOGGER.warn("Couldn't stop server listening on port: %d - %s", self.port, e)
            pass

    def run(self):
        try:
            self.__run_forever()
        except KeyboardInterrupt:
            self.LOGGER.info("Stopped listening on port: %d", self.port)
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)

    def stop(self):
        self.__running = False


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


webserver = WebServer(8080, ThreadingHTTPServer, HTTPHandler3)
webserver.run()
