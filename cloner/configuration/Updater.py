import os
import sys

from cloner.configuration.Configuration import ConfigurationReader, Configuration
from haproxy.HaProxy import HaProxy, Status


class Updater:
    def load(self):
        pass

    def check(self):
        pass

    def save(self):
        pass


class FileUpdater(Updater):
    __configuration = Configuration()
    __haproxy_monitors = {}

    def __init__(self, configuration_path):
        self.configuration_path = configuration_path

    def load(self):
        self.__configuration = self.__load_configuration(self.configuration_path)
        self.__haproxy_monitors = self.__load_haproxy_monitors(self.__configuration)

    def __load_configuration(self, configuration_path):
        return ConfigurationReader.read(configuration_path)

    def __load_haproxy_monitors(self, configuration):
        haproxy_monitors = {}
        for name in configuration.get_haproxy_monitors_names():
            haproxy_monitor = configuration.get_haproxy_monitor(name)

            haproxy = HaProxy()
            haproxy.load_from_url(haproxy_monitor.url)

            haproxy_monitors[name] = haproxy

        return haproxy_monitors

    def check(self):
        for cluster_name in self.__configuration.get_clusters_names():
            cluster = self.__configuration.get_cluster(cluster_name)
            haproxy_monitor = self.get_haproxy_monitor(cluster.haproxy_backend_name)

            for hostdomain in cluster.get_hostdomains():
                host = cluster.get_host(hostdomain)
                hostname = self.get_hostname(hostdomain)

                self.is_available(haproxy_monitor, cluster.haproxy_backend_name, hostdomain)

    def is_available(self, haproxy_monitor, haproxy_backend_name, hostdomain):
        try:
            max_downtime_minutes = 20
            hostname = self.get_hostname(hostdomain)

            haproxy_host = haproxy_monitor.get_host(haproxy_backend_name, hostname)
            if haproxy_host.status == Status.DOWN and max_downtime_minutes < self.to_minutes(haproxy_host.last_status_change):
                return '[%s] Too long DOWN status (in minutes): %d > %d' % (
                    hostdomain, haproxy_host.last_status_change, max_downtime_minutes)
        except:
            return '[%s] Not found in proxy' % hostdomain

    def to_minutes(self, seconds):
        return int(seconds / 60)

    def get_hostname(self, hostdomain):
        split = hostdomain.split(".", 1)
        return split[0]

    def get_haproxy_monitor(self, haproxy_backend_name):
        return HaProxy.from_dict(self.__haproxy_monitors.get(haproxy_backend_name))


def main():
    configuration_path = "sample_configuration.json"

    updater = Updater()
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
