import json
import os

import sys


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


class Configuration(JsonMapper):
    def __init__(self, clusters: dict, haproxy_monitors: dict):
        self.clusters = clusters
        self.haproxy_monitors = haproxy_monitors

    def __str__(self):
        return "Configuration {" \
               "clusters: " + str(self.clusters) + ", " + \
               "haproxy_monitors: " + str(self.haproxy_monitors) + \
               "}"


class Cluster(Dict2Object):
    def __init__(self, name, haproxy_monitor=None, haproxy_backend_name=None, hosts={}, always_running=False, updater_enabled=False):
        self.name = name
        self.haproxy_monitor = haproxy_monitor
        self.haproxy_backend_name = haproxy_backend_name
        self.hosts = hosts
        self.always_running = always_running
        self.updater_enabled = updater_enabled

    def __str__(self):
        return "Cluster {" \
               "name: " + str(self.name) + ", " + \
               "haproxy_monitor: " + str(self.haproxy_monitor) + ", " + \
               "haproxy_backend_name: " + str(self.haproxy_backend_name) + ", " + \
               "hosts: " + str(self.hosts) + ", " + \
               "always_running: " + str(self.always_running) + ", " + \
               "updater_enabled: " + str(self.updater_enabled) + \
               "}"


class HaProxyMonitor(Dict2Object):
    def __init__(self, name, url):
        self.name = name
        self.url = url


class Host(Dict2Object):
    def __init__(self, host_domain, context_path=None, target_hosts=list(), listen_port=8080, allow_url_paths=list(),
                 disallow_url_paths=list(), url_rewrite_paths=list(), save_responses=False, traffic_rate='100%', http_timeout='20m'):
        self.host_domain = host_domain
        self.target_hosts = target_hosts
        self.traffic_rate = traffic_rate
        self.listen_port = listen_port
        self.allow_url_paths = allow_url_paths
        self.disallow_url_paths = disallow_url_paths
        self.url_rewrite_paths = url_rewrite_paths
        self.save_responses = save_responses
        self.http_timeout = http_timeout
        self.context_path = context_path


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


class HostAlreadyExists(Exception):
    pass


class ClusterAlreadyExists(Exception):
    pass


class ConfigurationManager:
    __configuration = Configuration({}, {})

    def __init__(self, path):
        self.path = path

    def read(self):
        self.__configuration = ConfigurationReader.read(self.path)

    def write(self):
        ConfigurationWriter.write(self.path, self.__configuration)

    def add_cluster(self, cluster: Cluster):
        if cluster.name in self.__configuration.clusters:
            raise ClusterAlreadyExists(cluster.name)

        self.__configuration.clusters[cluster.name] = cluster

    def get_clusters(self):
        return self.__configuration.clusters

    def get_cluster(self, name) -> Cluster:
        return self.__configuration.clusters[name]

    def add_host(self, cluster_name, host: Host):
        print("Add %s to %s" % (host.host_domain, cluster_name))

        if self.host_domain_exists(host.host_domain):
            raise HostAlreadyExists(host.host_domain)

        copy = self.get_cluster(cluster_name)
        copy.hosts[host.host_domain] = host

    def remove_host(self, cluster_name, host_domain):
        cluster = self.get_cluster(cluster_name)
        cluster.hosts.pop(host_domain)

    def host_domain_exists(self, host_domain):
        for cluster_name in self.__configuration.clusters.keys():
            if host_domain in self.get_cluster(cluster_name).hosts.keys():
                return True
        return False

    def get_host(self, cluster_name, host_domain):
        return self.get_cluster(cluster_name, host_domain)


def main():
    manager = ConfigurationManager("xxx.json")
    # manager.read()
    manager.add_cluster(Cluster("cluster-1"))
    manager.add_cluster(Cluster("cluster-2"))
    manager.add_cluster(Cluster("cluster-3"))
    manager.add_host("cluster-1", Host("host-1.domain.com"))
    manager.add_host("cluster-1", Host("host-2.domain.com"))
    manager.write()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
