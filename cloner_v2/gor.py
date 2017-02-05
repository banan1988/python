import os

from configuration import Configuration
from validator import Validator

__version__ = "0.1"

__all__ = ["GorArgs"]


def flat_array(array: list):
    # flat [[key, value], [key, value]]
    return [item for sublist in array for item in sublist]


class GorArgs:
    def __init__(self, configuration: Configuration, gor_path="./gor", as_root=True):
        self.gor_path = gor_path
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

    def _gor(self):
        if os.path.exists(self.gor_path):
            return [self.gor_path]
        raise Exception("Not found 'gor' application in path: %s" % self.gor_path)

    def get(self):
        args = []
        if self.as_root:
            args += ["sudo"]

        args += self._gor()

        if self.configuration:
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
