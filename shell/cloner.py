import argparse
import json
import logging
import os
import re
import threading
from logging import basicConfig
from logging.config import dictConfig
from subprocess import Popen, PIPE, CalledProcessError
from urllib.parse import urlparse


def flat_array(array: list):
    # flat [[key, value], [key, value]]
    return [item for sublist in array for item in sublist]


class Command:
    return_code = 0
    stdout = None
    stderr = None

    def __init__(self, command, timeout=None, shell=False):
        self.command = command
        self.timeout = timeout
        self.shell = shell

        self.proc = None

    def __str__(self):
        return "Command(" \
               "command=%s, " \
               "return_code=%d, " \
               "stdout=%s, " \
               "stderr=%s)" % (
                   self.command,
                   self.return_code,
                   self.stdout,
                   self.stderr
               )

    def execute(self):
        try:
            self.proc = Popen(self.command, stdout=PIPE, stderr=PIPE, shell=self.shell)
        except CalledProcessError as e:
            raise e
        except Exception as e:
            raise e
        else:
            with self.proc:
                self.proc.wait(self.timeout)

                self.return_code = self.proc.returncode
                self.stdout = self.proc.stdout.read().decode('utf-8').strip()
                self.stderr = self.proc.stderr.read().decode('utf-8').strip()

                return self
        finally:
            self.terminate()

    def terminate(self):
        if self.proc:
            self.proc.terminate()


class JsonMapper:
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    @classmethod
    def from_json(cls, json_str):
        json_dict = json.loads(json_str)
        return cls(**json_dict)


class Dict2Object:
    @classmethod
    def from_dict(cls, dictionary):
        if type(dictionary) is dict:
            return cls(**dictionary)
        return dictionary


class Paths(Dict2Object):
    """
    "paths": {
        "allow": [],
        "disallow": [],
        "rewrite": []
    }
    """

    def __init__(self, allow, disallow, rewrite):
        self.rewrite = rewrite
        self.disallow = disallow
        self.allow = allow


class Input(Dict2Object):
    """
    "input": {
        "port": 8080,
        "paths": {
            "allow": [],
            "disallow": [],
            "rewrite": []
        }
     },
    """

    def __init__(self, port, paths: Paths):
        self.paths = Paths.from_dict(paths)
        self.port = port


class Http(Dict2Object):
    """
    "http": {
        "hosts": [
            "http://a",
            "http://b",
            "http://c"
        ],
        "rate": "100%",
        "split_traffic": false,
        "workers": -1
    },
    """

    def __init__(self, hosts: list, rate, split_traffic: False, workers: -1):
        self.workers = workers
        self.split_traffic = split_traffic
        self.rate = rate
        self.hosts = hosts


class Output(Dict2Object):
    """
    "output": {
        "http": {
            "hosts": [
                "http://a",
                "http://b",
                "http://c"
            ],
            "rate": "100%",
            "split_traffic": false,
            "workers": -1
        },
        "stdout": false
    },
    """

    def __init__(self, http: Http, stdout=False):
        self.stdout = stdout
        self.http = Http.from_dict(http)


class Configuration(JsonMapper):
    def __init__(self, input: Input, output: Output, finish_after=None, extra_args=None):
        self.extra_args = extra_args
        self.finish_after = finish_after
        self.output = Output.from_dict(output)
        self.input = Input.from_dict(input)


class ConfigurationReader:
    @staticmethod
    def read(path) -> Configuration:
        with open(path) as configuration_file:
            return Configuration.from_json(configuration_file.read())


class Validator:
    @staticmethod
    def is_url(url):
        parsed_url = urlparse(url)
        return parsed_url.scheme in ["ftp", "http", "https"]

    @staticmethod
    def is_url_path(path):
        parsed_path = urlparse(path)
        return parsed_path.path and parsed_path.path.startswith("/")

    @staticmethod
    def is_regexp(regexp):
        try:
            re.compile(regexp)
            return True
        except re.error:
            return False

    @staticmethod
    def is_rewrite_path(rewrite_path):
        parts = rewrite_path.split(":")
        if len(parts) == 2:
            return Validator.is_regexp(parts[0])
        return False


class GorArgs:
    def __init__(self, configuration: Configuration, as_root=True):
        self.as_root = as_root
        self.configuration = configuration

    def _input_raw(self):
        if self.configuration.input.port <= 0:
            raise Exception("Port %s has to be greater than 0")
        return ["--input-raw", (":%d" % self.configuration.input.port)]

    def _append_rate(self, host):
        rate = self.configuration.output.http.rate
        if rate:
            return "%s|%s" % (host, rate)
        return host

    def _output_http(self, host):
        if Validator.is_url(host):
            return ["--output-http", self._append_rate(host)]
        raise Exception("Host %s has incorrect format" % host)

    def _output_https(self):
        target_hosts = self.configuration.output.http.hosts
        if len(target_hosts) == 0:
            raise Exception("List of hosts is empty")

        output_https = []
        for target_host in target_hosts:
            output_https += self._output_http(target_host)
        return output_https

    def _output_stdout(self):
        if self.configuration.output.stdout:
            return ["--output-stdout", "true"]
        return []

    def _exit_after(self):
        if self.configuration.finish_after:
            return ["--exit-after", self.configuration.finish_after]
        return []

    def _split_output(self):
        if self.configuration.output.http.split_traffic:
            return ["--split-output", "true"]
        return []

    def _http_allow_url(self, path):
        if Validator.is_url_path(path):
            return ["--http-allow-url", path]
        raise Exception("Allow path %s has incorrect format" % path)

    def _http_allow_urls(self):
        allow_urls = [self._http_allow_url(path) for path in self.configuration.input.paths.allow]
        return flat_array(allow_urls)

    def _http_disallow_url(self, path):
        if Validator.is_url_path(path):
            return ["--http-disallow-url", path]
        raise Exception("Disallow path %s has incorrect format" % path)

    def _http_disallow_urls(self):
        disallow_urls = [self._http_disallow_url(path) for path in self.configuration.input.paths.disallow]
        return flat_array(disallow_urls)

    def _http_rewrite_url(self, rewrite_path):
        if not Validator.is_rewrite_path(rewrite_path):
            raise Exception("Rewrite path %s has incorrect format. Expects ':' as a delimiter." % rewrite_path)
        return ["--http-rewrite-url", rewrite_path]

    def _http_rewrite_urls(self):
        rewrite_urls = [self._http_rewrite_url(path) for path in self.configuration.input.paths.rewrite]
        return flat_array(rewrite_urls)

    def _output_http_workers(self):
        # (Average number of requests per second)/(Average target response time per second)
        if self.configuration.output.http.workers >= 1:
            return ["--output-http-workers", self.configuration.output.http.workers]
        return []

    def _extra_args(self):
        if self.configuration.extra_args:
            extra_args = [[key, value] for key, value in self.configuration.extra_args.items()]
            return flat_array(extra_args)
        return []

    def get(self):
        args = []
        if self.as_root:
            args += ["sudo"]

        args += ["gor"]

        args += self._input_raw()
        args += self._http_allow_urls()
        args += self._http_disallow_urls()
        args += self._http_rewrite_urls()

        args += self._output_https()
        args += self._output_stdout()

        args += self._split_output()
        args += self._output_http_workers()

        args += self._exit_after()
        args += self._extra_args()

        return args


class Cloner:
    def __init__(self, configuration: Configuration):
        self.cloner_thread = None
        gor_args = GorArgs(configuration).get()
        command_args = []
        command_args += gor_args
        self.command = Command(command_args)

    def start(self):
        self.cloner_thread = threading.Thread(
            name="ClonerThread",
            target=self.command.execute,
            daemon=True
        )
        self.cloner_thread.start()

    def wait_for_thread(self):
        self.cloner_thread.join()

    def stop(self):
        self.command.terminate()
        self.wait_for_thread()


def get_args():
    parser = argparse.ArgumentParser(
        description='Cloner',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--configuration-path', type=str,
                        required=True,
                        help='Path to configuration.')
    return parser.parse_args()


def setup_logging(
        path='logging.json',
        default_level=logging.INFO
):
    """
    Setup logging configuration
    """
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        dictConfig(config)
    else:
        basicConfig(level=default_level)


if __name__ == '__main__':
    try:
        setup_logging()
        ARGS = get_args()

        configuration = ConfigurationReader.read(ARGS.configuration_path)
        cloner = Cloner(configuration)
        cloner.start()
        cloner.wait_for_thread()
    except SystemExit:
        logging.error('SystemExit', exc_info=True)
        raise
    except KeyboardInterrupt:
        logging.error('KeyboardInterrupt', exc_info=True)
        raise
    except Exception as e:
        logging.error('Error', exc_info=True)
        raise
    finally:
        cloner.stop()
