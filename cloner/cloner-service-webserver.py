import argparse
import json
import logging
import logging.config
import logging.handlers
import os
import sys
from string import Template
from subprocess import Popen, PIPE, CalledProcessError

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
        return logging.getLogger('file')
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


def utf8(data):
    return data.decode('utf-8')


class ShellCommand:
    returncode = 0
    stdout = None
    stderr = None

    def __init__(self, command):
        self.command = command

    def __str__(self):
        return "ShellCommand(" \
               "command=%s, " \
               "returncode=%d, " \
               "stdout=%s, " \
               "stderr=%s)" % (
                   self.command,
                   self.returncode,
                   self.stdout,
                   self.stderr
               )

    def execute(self):
        p = None
        try:
            p = Popen(self.command, stdout=PIPE, stderr=PIPE, shell=True)
            p.wait()

            self.returncode = p.returncode
            self.stdout = utf8(p.stdout.read()).strip()
            self.stderr = utf8(p.stderr.read()).strip()
        except CalledProcessError as e:
            raise Exception("Couldn't execute command: %s - %s" % (self.command, e.output))
        except Exception as e:
            raise Exception("Couldn't execute command: %s - %s" % (self.command, e))
        finally:
            if p:
                try:
                    p.kill()
                except OSError as e:
                    LOGGER.debug("Couldn't kill process: %s - %s", p.pid, e)
                    pass


def run(port, server_class=HTTPServer, handler_class=BaseHTTPRequestHandler):
    server_address = ('', port)
    httpd = None
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
    start = ShellCommand('gor')
    stop = ShellCommand('gor')
    restart = ShellCommand('gor')
    status = ShellCommand('gor')
    version = ShellCommand('gor')

    def do_GET(self):
        try:
            if self.path == "/":
                self.send_response(200)
                self.send_headers({"Content-type": "text/html; charset=utf-8"})

                content = self.get_content_from_file("templates/index.html")

                self.send_content(content)
                return

            if self.path == "/start":
                self.send_response(200)
                self.send_headers({"Content-type": "text/plain; charset=utf-8"})

                self.send_content("start")
                return

            if self.path == "/stop":
                self.send_response(200)
                self.send_headers({"Content-type": "text/plain; charset=utf-8"})

                self.send_content("stop")
                return

            if self.path == "/restart":
                self.send_response(200)
                self.send_headers({"Content-type": "text/plain; charset=utf-8"})

                self.send_content("restart")
                return

            if self.path == "/status":
                self.send_response(200)
                self.send_headers({"Content-type": "application/json; charset=utf-8"})

                self.version.execute()
                content = self.get_json_content("STATUS", self.version)
                self.send_content(content)
                return

            if self.path == "/version":
                self.send_response(200)
                self.send_headers({"Content-type": "application/json; charset=utf-8"})

                self.version.execute()
                content = json.dumps({
                    "action": "VERSION",
                    "status": "OK",
                    "details": self.version.stdout
                })
                self.send_content(content)
                return

        except Exception as e:
            self.send_error_500(e)
            return

        self.send_error_404()
        return

    def get_json_content(self, action, command_result):
        if self.version.returncode == 0:
            content = {
                "action": action,
                "status": "OK",
                "details": command_result.stdout
            }
        else:
            content = {
                "action": action,
                "status": "ERROR",
                "details": command_result.stderr
            }
        return json.dumps(content)


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
