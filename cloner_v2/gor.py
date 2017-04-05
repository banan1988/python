import os

from configuration import Configuration
from configuration import ConfigurationReader
from configuration import InputType

from validator import Validator

__version__ = "0.1"

__all__ = ["GorCommand"]


def flat_array(array: list):
    # flat [[key, value], [key, value]]
    return [item for sublist in array for item in sublist]


class GorCommandException(Exception):
    pass


class GorCommand:
    def __init__(self, configuration: Configuration, gor_path="./gor", as_root=True):
        self.gor_path = gor_path
        self.as_root = as_root
        self.configuration = configuration

    def _input_tcp(self):
        if InputType.TCP == self.configuration.input.type:
            if self.configuration.input.port > 0:
                return ["--input-tcp", (":%d" % self.configuration.input.port)]
            raise GorCommandException("TCP port %s has to be greater than 0" % self.configuration.input.port)
        return []

    def _input_raw(self):
        if InputType.RAW == self.configuration.input.type:
            if self.configuration.input.port > 0:
                return ["--input-raw", (":%d" % self.configuration.input.port)]
            raise GorCommandException("RAW port %s has to be greater than 0" % self.configuration.input.port)
        return []

    def _append_rate(self, host, global_rate):
        if host.get("rate", None):
            return '"%s|%s"' % (host["host"], host["rate"])
        elif global_rate:
            return '"%s|%s"' % (host["host"], global_rate)
        return '"%s"' % host["host"]

    def _output_tcp(self, host):
        host_port = host["host"].split(":")
        if len(host_port) < 2:
            hostname = host["host"]
        else:
            hostname = host_port[0]

        if Validator.is_hostname(hostname):
            return ["--output-tcp", self._append_rate(host, self.configuration.output.tcp.rate)]
        raise GorCommandException("Output's TCP host %s has incorrect format" % host["host"])

    def _output_tcps(self):
        if not self.configuration.output.tcp:
            return []

        target_hosts = self.configuration.output.tcp.hosts
        if len(target_hosts) == 0:
            raise GorCommandException("List of output's TCP hosts is empty")

        output_tcps = []
        for target_host in target_hosts:
            output_tcps += self._output_tcp(target_host)
        return output_tcps

    def _output_http(self, host):
        if Validator.is_url(host["host"]):
            return ["--output-http", self._append_rate(host, self.configuration.output.http.rate)]
        raise GorCommandException("Output's HTTP host %s has incorrect format" % host["host"])

    def _output_https(self):
        if not self.configuration.output.http:
            return []

        target_hosts = self.configuration.output.http.hosts
        if len(target_hosts) == 0:
            raise GorCommandException("List of output's HTTP hosts is empty")

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
        if self.configuration.output.split_traffic:
            return ["--split-output", "true"]
        return []

    def _http_allow_url(self, path):
        if Validator.is_url_path(path):
            return ["--http-allow-url", '"%s"' % path]
        raise GorCommandException("Allow path %s has incorrect format" % path)

    def _http_allow_urls(self):
        if not self.configuration.input.paths:
            return []

        allow_urls = [self._http_allow_url(path) for path in self.configuration.input.paths.allow]
        return flat_array(allow_urls)

    def _http_disallow_url(self, path):
        if Validator.is_url_path(path):
            return ["--http-disallow-url", '"%s"' % path]
        raise GorCommandException("Disallow path %s has incorrect format" % path)

    def _http_disallow_urls(self):
        if not self.configuration.input.paths:
            return []

        disallow_urls = [self._http_disallow_url(path) for path in self.configuration.input.paths.disallow]
        return flat_array(disallow_urls)

    def _http_rewrite_url(self, rewrite_path):
        if Validator.is_rewrite_path(rewrite_path):
            return ["--http-rewrite-url", '"%s"' % rewrite_path]
        raise GorCommandException("Rewrite path %s has incorrect format. Expects ':' as a delimiter." % rewrite_path)

    def _http_rewrite_urls(self):
        if not self.configuration.input.paths:
            return []

        rewrite_urls = [self._http_rewrite_url(path) for path in self.configuration.input.paths.rewrite]
        return flat_array(rewrite_urls)

    def _output_http_workers(self):
        # (Average number of requests per second)/(Average target response time per second)
        if self.configuration.output.http.workers >= 1:
            return ["--output-http-workers", str(self.configuration.output.http.workers)]
        return []

    def _extra_args(self):
        if self.configuration.extra_args:
            extra_args = [[key, '"%s"' % value] for key, value in self.configuration.extra_args.items()]
            return flat_array(extra_args)
        return []

    def _gor(self):
        if os.path.exists(self.gor_path):
            return [self.gor_path]
        raise GorCommandException("Not found 'gor' application in path: %s" % self.gor_path)

    def build(self):
        args = []

        if self.as_root:
            args += ["sudo"]

        args += self._gor()

        if self.configuration:
            args += self._input_raw()
            args += self._input_tcp()

            args += self._http_allow_urls()
            args += self._http_disallow_urls()
            args += self._http_rewrite_urls()

            args += self._output_https()
            args += self._output_http_workers()
            args += self._output_tcps()

            args += self._split_output()
            args += self._output_stdout()

            args += self._exit_after()
            args += self._extra_args()

        return args

    def build_string(self):
        return " ".join(self.build())
