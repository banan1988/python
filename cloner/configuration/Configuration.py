import json


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
        return cls(**dictionary)


class Host(Dict2Object):
    hostdomain = None

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

    def get_hostname(self):
        split = self.hostdomain.split(".", 1)
        return split[0]

    def get_domain(self):
        split = self.hostdomain.split(".")
        return split[1:]


class Cluster(Dict2Object):
    name = None

    def __init__(self, always_running=False, updater_enabled=True, haproxy_monitor=None, haproxy_backend_name=None, hosts={}):
        self.always_running = always_running
        self.updater_enabled = updater_enabled
        self.haproxy_monitor = haproxy_monitor
        self.haproxy_backend_name = haproxy_backend_name
        self.hosts = hosts

    def add_host(self, hostdomain, host):
        self.hosts[hostdomain] = host

    def add_hosts(self, hostdomains, host):
        for hostdomain in hostdomains:
            self.add_host(hostdomain, host)

    def get_hosts(self):
        return self.hosts

    def get_hostdomains(self):
        return self.hosts.keys()

    def get_host(self, hostdomain):
        host = Host.from_dict(self.hosts.get(hostdomain))
        host.hostdomain = hostdomain
        return host


class HaProxyMonitor(Dict2Object):
    name = None

    def __init__(self, url):
        self.url = url


class Configuration(JsonMapper):
    def __init__(self, clusters={}, haproxy_monitors={}):
        self.clusters = clusters
        self.haproxy_monitors = haproxy_monitors

    def add_cluster(self, name, cluster):
        self.clusters[name] = cluster

    def add_haproxy_monitor(self, name, haproxy_monitor):
        self.haproxy_monitors[name] = haproxy_monitor

    def get_clusters(self):
        return self.clusters

    def get_clusters_names(self):
        return self.clusters.keys()

    def get_cluster(self, name):
        cluster = Cluster.from_dict(self.clusters.get(name))
        cluster.name = name
        return cluster

    def get_haproxy_monitors(self):
        return self.haproxy_monitors

    def get_haproxy_monitors_names(self):
        return self.haproxy_monitors.keys()

    def get_haproxy_monitor(self, name):
        haproxy_monitor = HaProxyMonitor.from_dict(self.haproxy_monitors.get(name))
        haproxy_monitor.name = name
        return haproxy_monitor


class ConfigurationReader:
    @staticmethod
    def read(path):
        with open(path) as configuration_file:
            return Configuration.from_json(configuration_file.read())


class ConfigurationWriter:
    @staticmethod
    def write(path, configuration):
        with open(path, "w") as configuration_file:
            configuration_file.write(configuration.to_json())


configuration = Configuration()
monitor = HaProxyMonitor("http://localhost:9090/content/csv")
monitor.name = "xxx"
configuration.add_haproxy_monitor("localhost-8080", monitor)
configuration.add_haproxy_monitor("localhost-9090", monitor)

cluster = Cluster()
cluster.always_running = True
cluster.haproxy_backend_name = "backend-name-1"
cluster.haproxy_monitor = "localhost-9090"

host = Host()
cluster.add_host("localhost.domain", host)
cluster.add_hosts(("localhost-1.domain", "localhost-2.domain"), host)

configuration.add_cluster("cluster-1", cluster)
configuration.add_cluster("cluster-2", cluster)

ConfigurationWriter.write("sample_configuration.json", configuration)

hpm = HaProxyMonitor("url")
hpm.name = "xxx"
print(hpm)
