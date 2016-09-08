import os
import sys

from cloner.configuration.Configuration import ConfigurationReader, Configuration
from haproxy.HaProxy import HaProxy, Status


class HostToUpdate:
    def __init__(self, cluster_name, hostdomain, reason):
        self.cluster_name = cluster_name
        self.hostdomain = hostdomain
        self.reason = reason


class ConfigurationUpdater:
    def load(self):
        pass

    def check(self):
        pass

    def save(self):
        pass


class NotFoundHaProxyMonitor(Exception):
    pass


class FileConfigurationUpdater(ConfigurationUpdater):
    max_downtime_minutes = 20

    __configuration = Configuration()
    __haproxy_monitors = {}
    __hosts_to_update = {}

    def __init__(self, configuration_path):
        self.configuration_path = configuration_path
        print(configuration_path)

    def load(self):
        self.__configuration = self.__load_configuration()
        print("Loaded configuration")
        self.__haproxy_monitors = self.__load_haproxy_monitors()
        print("Loaded HaProxy monitors")

    def __load_configuration(self):
        return ConfigurationReader.read(self.configuration_path)

    def __load_haproxy_monitors(self):
        haproxy_monitors = {}
        for name in self.__configuration.get_haproxy_monitors_names():
            print(name)
            haproxy_monitor = self.__configuration.get_haproxy_monitor(name)

            haproxy = HaProxy()
            haproxy.load_from_url(haproxy_monitor.url)

            haproxy_monitors[name] = haproxy
            print("Loaded HaProxy monitor for %s " % name)

        return haproxy_monitors

    def check(self):
        for cluster_name in self.__configuration.get_clusters_names():
            cluster = self.__configuration.get_cluster(cluster_name)

            if cluster.updater_enabled:
                try:
                    self.__hosts_to_update[cluster.name] = self.get_hosts_to_update(cluster)
                except Exception as e:
                    print("Couldn't get hosts to update for %s cluster - %s" % (cluster.name, e))

    def get_hosts_to_update(self, cluster):
        hosts_to_update = []

        haproxy_monitor = self.get_haproxy_monitor(cluster.haproxy_monitor)
        for hostdomain in cluster.get_hostdomains():
            host_to_update = self.host_to_update(haproxy_monitor, cluster, hostdomain)
            if host_to_update:
                hosts_to_update.append(host_to_update)

        return hosts_to_update

    def host_to_update(self, haproxy_monitor, cluster, hostdomain):
        host = cluster.get_host(hostdomain)

        try:
            if not self.host_is_available_in_haproxy(haproxy_monitor, cluster.haproxy_backend_name, host.get_hostname()):
                reason = 'Host %s is DOWN longer than %d' % (host.hostdomain, self.max_downtime_minutes)
                return HostToUpdate(cluster.name, host.hostdomain, reason)
            return None
        except:
            reason = 'Not found host %s in proxy' % host.hostdomain
            return HostToUpdate(cluster.name, host.hostdomain, reason)

    def host_is_available_in_haproxy(self, haproxy_monitor, haproxy_backend_name, hostname):
        haproxy_host = haproxy_monitor.get_host(haproxy_backend_name, hostname)
        if haproxy_host.status == Status.DOWN and self.max_downtime_minutes < self.to_minutes(haproxy_host.last_status_change):
            return False
        return True

    def to_minutes(self, seconds):
        return int(seconds / 60)

    def get_haproxy_monitor(self, name):
        if name not in self.__haproxy_monitors.keys():
            raise NotFoundHaProxyMonitor("Not found HaProxy monitor by name %s in loaded HaProxy monitors %s. Please check configuration."
                                         % (name, ",".join(self.__haproxy_monitors.keys())))
        return self.__haproxy_monitors.get(name)


def main():
    configuration_path = "sample_configuration.json"

    updater = FileConfigurationUpdater(configuration_path)
    updater.load()
    updater.check()
    updater.save()

    pass


if __name__ == '__main__':
    # ARGS = get_args()
    # LOGGER = get_logger()

    try:
        main()
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
