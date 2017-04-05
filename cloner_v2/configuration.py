import json

__version__ = "0.1"

__all__ = ["Configuration", "ConfigurationReader"]


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


class InputType:
    RAW = "raw"
    TCP = "tcp"


class Input(Dict2Object):
    """
    "input": {
        "type": "raw"
        "port": 8080,
        "paths": {
            "allow": [],
            "disallow": [],
            "rewrite": []
        }
     },
    """

    def __init__(self, type: InputType, port, paths: Paths):
        self.type = type
        self.port = port
        self.paths = Paths.from_dict(paths)


class Http(Dict2Object):
    """
    "http": {
        "hosts": [
            "http://a",
            "http://b",
            "http://c"
        ],
        "rate": "100%",
        "workers": -1
    },
    """

    def __init__(self, hosts: list, rate=None, workers=-1):
        self.hosts = hosts
        self.rate = rate
        self.workers = workers


class Tcp(Dict2Object):
    """
    "tcp": {
        "hosts": [
            "http://a",
            "http://b",
            "http://c"
        ],
        "rate": "100%",
    },
    """

    def __init__(self, hosts: list, rate=None):
        self.hosts = hosts
        self.rate = rate


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

    def __init__(self, http: Http, tcp: Tcp, split_traffic=False, stdout=False):
        self.http = Http.from_dict(http)
        self.tcp = Tcp.from_dict(tcp)
        self.split_traffic = split_traffic
        self.stdout = stdout


class Configuration(JsonMapper):
    def __init__(self, input: Input, output: Output, finish_after=None, extra_args=None):
        self.extra_args = extra_args
        self.finish_after = finish_after
        self.output = Output.from_dict(output)
        self.input = Input.from_dict(input)


class ConfigurationReader:
    @staticmethod
    def read(path) -> Configuration:
        try:
            with open(path) as configuration_file:
                return Configuration.from_json(configuration_file.read())
        except FileNotFoundError as e:
            raise Exception("Couldn't open file (%s): %s." % (path, e))
        except ValueError as e:
            raise Exception("Configuration file (%s) has incorrect format: %s." % (path, e))
        except TypeError as e:
            raise Exception("Couldn't parse configuration file (%s): %s." % (path, e))
