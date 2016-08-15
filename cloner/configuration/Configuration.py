import json


class JSONSerializer:
    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    @classmethod
    def from_JSON(cls, json_str):
        json_dict = json.loads(json_str)
        return cls(**json_dict)


class Dict2Obj(object):
    def __init__(self, dictionary):
        for key in dictionary:
            setattr(self, key, dictionary[key])

    def __repr__(self):
        attrs = str([x for x in self.__dict__])
        return "<Dict2Obj: %s>" % attrs


class HostConfiguraton:
    def __init__(self, target_hosts=[], traffic_rate='100%', listen_port=8080, allow_url_paths=[],
                 disallow_url_paths=[], url_rewrite_paths=[], save_responses=False, http_timeout='20m',
                 context_path=None):
        self.target_hosts = target_hosts
        self.traffic_rate = traffic_rate
        self.listen_port = listen_port
        self.allow_url_paths = allow_url_paths
        self.disallow_url_paths = disallow_url_paths
        self.url_rewrite_paths = url_rewrite_paths
        self.save_responses = save_responses
        self.http_timeout = http_timeout
        self.context_path = context_path


class ClusterConfiguration:
    def __init__(self, always_running=False, haproxy_monitor=None, haproxy_backend_name=None, hosts={}):
        self.always_running = always_running
        self.haproxy_monitor = haproxy_monitor
        self.haproxy_backend_name = haproxy_backend_name
        self.hosts = hosts

    # @classmethod
    # def from_dict(cls, dictionary):
    #     return cls(**dictionary)

    def add_host(self, hostdomain, host_configuration):
        self.hosts[hostdomain] = host_configuration

    def add_hosts(self, hostdomains, host_configuration):
        for hostdomain in hostdomains:
            self.add_host(hostdomain, host_configuration)

    def get_host(self, hostdomain):
        return self.hosts[hostdomain]

    def get_hosts(self):
        return self.hosts


class HaProxyMonitor:
    def __init__(self, name, url):
        self.name = name
        self.url = url


class Configuration(JSONSerializer):
    def __init__(self, clusters={}, haproxy_monitors={}):
        self.clusters = clusters
        self.haproxy_monitors = haproxy_monitors

    def add_cluster(self, name, cluster):
        self.clusters[name] = cluster

    def add_haproxy_monitor(self, name, url):
        self.haproxy_monitors[name] = url

    def get_clusters(self):
        return self.clusters

    def get_cluster(self, name):
        return ClusterConfiguration(self.clusters.get(name))

    def get_haproxy_monitors(self):
        return self.haproxy_monitors

    def get_haproxy_monitor(self, name):
        return self.haproxy_monitors[name]


class ConfigurationReader:
    @staticmethod
    def read(path):
        with open(path) as configuration_file:
            return Configuration.from_JSON(configuration_file.read())


class ConfigurationWriter:
    @staticmethod
    def write(path, configuration):
        with open(path, "w") as configuration_file:
            configuration_file.write(configuration.to_JSON())


configuration = Configuration()
configuration.add_haproxy_monitor("localhost-8080", "http://localhost:8080/monitor")
configuration.add_haproxy_monitor("localhost-9090", "http://localhost:9090/monitor")

cluster = ClusterConfiguration()
cluster.always_running = True
cluster.haproxy_backend_name = "backend-name-1"
cluster.haproxy_monitor = "localhost"

host_configuration = HostConfiguraton()
cluster.add_host("localhost.domain", host_configuration)
cluster.add_hosts(("localhost-1.domain", "localhost-2.domain"), host_configuration)

configuration.add_cluster("cluster-1", cluster)
configuration.add_cluster("cluster-2", cluster)

ConfigurationWriter.write("sample_configuration.json", configuration)
