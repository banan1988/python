from enum import Enum
from http.server import HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
from string import Template
import argparse
import logging
import logging.config
import logging.handlers
import sys
import os

PORT = 8000


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
                        default=PORT,
                        help='Port to listening.')
    return parser.parse_args()


def run(port=PORT, server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    try:
        LOGGER.info("Listening on port: %d", port)
        httpd.serve_forever()
    except Exception as e:
        httpd.shutdown()


class MimeType(Enum):
    text_html = "text/html"
    text_css = "text/css"


class HeaderType(Enum):
    content_type = "Content-type"
    allow_control_allow_origin = "Access-Control-Allow-Origin"


class Header:
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __str__(self):
        return "%s: %s" % (self.key, self.value)

        # contentType = Header("Content-type", "text/html; charset=utf-8")
        # accessControlAllowOrigin = Header("Access-Control-Allow-Origin", "*")
        #
        # headers = [contentType, accessControlAllowOrigin]


class HTTPHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)

            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            f = open("index.html")
            template = Template(f.read())
            index = template.safe_substitute(dict(message="hello"))

            # self.send_response(200, "hello")

            # self.wfile.write(bytes("index", "utf-8"))
            self.wfile.write(bytes(index, "utf-8"))
            return
            #
            # if self.path == "/":
            #     self.path = "/index_example2.html"
            #
            # try:
            #     sendReply = False
            #     if self.path.endswith(".html"):
            #         mimetype = MimeType.text_html
            #         sendReply = True
            #     if self.path.endswith(".jpg"):
            #         mimetype = 'image/jpg'
            #         sendReply = True
            #     if self.path.endswith(".gif"):
            #         mimetype = 'image/gif'
            #         sendReply = True
            #     if self.path.endswith(".js"):
            #         mimetype = 'application/javascript'
            #         sendReply = True
            #     if self.path.endswith(".css"):
            #         mimetype = MimeType.text_css
            #         sendReply = True
            #
            #     if sendReply == True:
            #         # Open the static file requested and send it
            #         # f = open(curdir + sep + self.path)
            #         self.send_response(200)
            #         self.send_header('Content-type', mimetype)
            #         self.end_headers()
            #         self.wfile.write(bytes("message", "utf8"))
            #         # self.wfile.write(f.read())
            #         # f.close()
            #     return
            # except IOError:
            #     self.send_error(404, 'File Not Found: %s' % self.path)

            # def setHeaders(self, Header):
        if self.path == "/content/text":
            self.response_file_as_content("content.txt")
            return

        if self.path == "/content/html":
            self.response_file_as_content("content.html", 499, "text/html")
            return

        if self.path == "/content/json":
            self.response_file_as_content("content.json", 200, "application/json")
            return

    def response_file_as_content(self, filename, code=200, mime_type="text/plain"):
        self.send_response(code)
        self.header(mime_type)
        with open("responses/%s" % filename) as content:
            self.content(content)

    def header(self, mime_type="text/plain"):
        self.send_header("Content-type", "%s; charset=utf-8" % mime_type)
        self.end_headers()

    def content(self, content):
        if str == type(content):
            self.wfile.write(bytes(content, "utf8"))
        else:
            self.wfile.write(bytes(content.read(), "utf8"))


def main():
    run(ARGS.port, HTTPServer, HTTPHandler)

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
