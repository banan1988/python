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
        if type(dictionary) is dict:
            return cls(**dictionary)
        return dictionary


class Configuration(JsonMapper):
    def __init__(self, clusters: dict, replayers: dict, haproxy_monitors: dict):
        self.clusters = clusters
        self.replayers = replayers
        self.haproxy_monitors = haproxy_monitors


class Cluster(Dict2Object):
    def __init__(self, name, hosts: dict, haproxy_monitor, haproxy_backend_name=None, always_running=False, updater_enabled=False):
        self.name = name
        self.hosts = hosts
        self.haproxy_monitor = haproxy_monitor
        self.haproxy_backend_name = haproxy_backend_name
        self.always_running = always_running
        self.updater_enabled = updater_enabled


class HaProxyMonitor(Dict2Object):
    def __init__(self, name, url):
        self.name = name
        self.url = url


class Host(Dict2Object):
    def __init__(self, host_domain, target_hosts: list, allow_url_paths: list, listen_port=8080, context_path=None,
                 disallow_url_paths: list = None, url_rewrite_paths: list = None, save_responses=False, traffic_rate='100%', http_timeout='20m'):
        self.host_domain = host_domain
        self.target_hosts = target_hosts
        self.traffic_rate = traffic_rate
        self.listen_port = listen_port

        if allow_url_paths:
            self.allow_url_paths = allow_url_paths
        else:
            self.allow_url_paths = list()

        if disallow_url_paths:
            self.disallow_url_paths = disallow_url_paths
        else:
            self.disallow_url_paths = list()

        self.url_rewrite_paths = url_rewrite_paths
        self.save_responses = save_responses
        self.http_timeout = http_timeout
        self.context_path = context_path


class ConfigurationReader:
    @staticmethod
    def read(path) -> Configuration:
        with open(path) as configuration_file:
            return Configuration.from_json(configuration_file.read())


class ConfigurationWriter:
    @staticmethod
    def write(path, configuration: Configuration):
        with open(path, "w") as configuration_file:
            configuration_file.write(configuration.to_json())


class HostAlreadyExists(Exception):
    pass


class ClusterAlreadyExists(Exception):
    pass


class HaProxyMonitorAlreadyExists(Exception):
    pass


class ValidationException(Exception):
    pass


class ConfigurationManager:
    __configuration = Configuration({}, {}, {})

    def __init__(self, path):
        self.path = path

    def read(self):
        self.__configuration = ConfigurationReader.read(self.path)
        # self.validate()

    def write(self):
        ConfigurationWriter.write(self.path, self.__configuration)

    def validate(self):
        for key_name in self.get_clusters().keys():
            name = self.get_cluster(key_name).hosts
            print(name)
            if key_name != name:
                raise ValidationException("Key %s is different that name in cluster: %s" % (key_name, name))

        for key_name in self.get_haproxy_monitors().keys():
            name = self.get_haproxy_monitor(key_name).name
            if key_name != name:
                raise ValidationException("Key %s is different that name in haproxy monitor: %s" % (key_name, name))

    def add_cluster(self, cluster: Cluster):
        print("Add cluster %s" % cluster.name)

        if cluster.name in self.get_clusters():
            raise ClusterAlreadyExists(cluster.name)

        self.__configuration.clusters[cluster.name] = cluster

    def get_clusters(self):
        return self.__configuration.clusters

    def get_cluster(self, name) -> Cluster:
        return Cluster.from_dict(self.get_clusters().get(name))

    def get_hosts(self, cluster_name):
        return self.get_cluster(cluster_name).hosts

    def get_host(self, cluster_name, host_domain) -> Host:
        return self.get_hosts(cluster_name).get(host_domain)

    def add_host(self, cluster_name, host: Host):
        print("Add host %s to cluster %s" % (host.host_domain, cluster_name))

        if self.host_domain_exists(host.host_domain):
            raise HostAlreadyExists(host.host_domain)

        self.get_cluster(cluster_name).hosts[host.host_domain] = host

    def remove_host(self, cluster_name, host_domain):
        self.get_hosts(cluster_name).pop(host_domain)

    def host_domain_exists(self, host_domain):
        for cluster_name in self.get_clusters().keys():
            if host_domain in self.get_cluster(cluster_name).hosts.keys():
                return True
        return False

    def add_haproxy_monitor(self, haproxy_monitor: HaProxyMonitor):
        print("Add HaProxyMonitor %s" % haproxy_monitor.name)

        if haproxy_monitor.name in self.get_haproxy_monitors():
            raise HaProxyMonitorAlreadyExists(haproxy_monitor.name)

        self.__configuration.haproxy_monitors[haproxy_monitor.name] = haproxy_monitor

    def get_haproxy_monitors(self):
        return self.__configuration.haproxy_monitors

    def get_haproxy_monitor(self, name) -> HaProxyMonitor:
        return self.get_haproxy_monitors().get(name)


def main():
    manager = ConfigurationManager("xxx.json")
    manager.read()

    monitor = HaProxyMonitor("localhost-9091", "http://localhost:9091/content/csv")
    manager.add_haproxy_monitor(monitor)

    manager.add_cluster(Cluster("cluster-4", hosts={"host-1.domain.com": Host("host-1.domain.com", "", "")}, haproxy_monitor=monitor.name))
    manager.add_cluster(Cluster("cluster-5", hosts={}, haproxy_monitor=monitor.name))
    manager.add_cluster(Cluster("cluster-6", hosts={}, haproxy_monitor=monitor.name))
    manager.add_host("cluster-4", Host("host-5.domain.com", "", ""))
    manager.add_host("cluster-5", Host("host-6.domain.com", "", ""))
    manager.add_host("cluster-6", Host("host-7.domain.com", "", ""))
    manager.write()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
