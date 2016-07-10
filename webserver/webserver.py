import argparse
import logging
import logging.config
import logging.handlers
import os
import sys

from string import Template

try:
    # python 3
    from http.server import HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
except ImportError:
    # python 2
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
    from SimpleHTTPServer import SimpleHTTPRequestHandler


def get_default_logger():
    # create logger
    logger = logging.getLogger('default')
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to handler
    handler.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(handler)
    return logger


def get_logger():
    try:
        logging.config.fileConfig('logging.conf')
        return logging.getLogger('mixed')
    except Exception as e:
        print(e)
        return get_default_logger()


def get_args():
    parser = argparse.ArgumentParser(
        description='Simple webserver written in Python',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--port', type=int,
                        required=True,
                        help='Port to listening.')
    return parser.parse_args()


def run(port, server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    server_address = ('', port)
    httpd = None;
    try:
        httpd = server_class(server_address, handler_class)

        LOGGER.info("Listening on port: %d", port)
        httpd.serve_forever()
    except Exception as e:
        LOGGER.warn("Couldn't start webserver on port: %d -  %s", port, e)
    finally:
        if httpd:
            httpd.shutdown()


class DefaultHTTPHandler(SimpleHTTPRequestHandler):
    def send_headers(self, parameters):
        assert type(parameters) == dict

        for key, value in parameters.items():
            self.send_header(key, value)

        self.end_headers()

    def send_content(self, content):
        self.wfile.write(content)

    def send_error_404(self):
        error_msg = "Not Found resources under %s path" % self.path
        LOGGER.warn(error_msg)
        self.send_error(404, error_msg)

    def send_error_500(self, e):
        error_msg = "Couldn't handle request for path: %s - %s" % (self.path, e)
        LOGGER.warn(error_msg)
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


class HTTPHandler2(DefaultHTTPHandler):
    """python 2"""

    def do_GET(self):
        try:
            if self.path == "/":
                self.send_response(200)
                self.send_headers({"Content-type": "text/html; charset=utf-8"})

                content = self.get_content_from_template("index.html", dict(message="Hello"))

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


class HTTPHandler3(DefaultHTTPHandler):
    """python 3"""

    def do_GET(self):
        try:
            if self.path == "/":
                self.send_response(200)
                self.send_headers({"Content-type": "text/html; charset=utf-8"})

                content = self.get_content_from_template("index.html", dict(message="Hello"))

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


def main():
    run(ARGS.port, HTTPServer, HTTPHandler2)


if __name__ == '__main__':
    ARGS = get_args()
    LOGGER = get_logger()

    try:
        main()
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
