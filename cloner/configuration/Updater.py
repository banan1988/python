from cloner.configuration.Configuration import ConfigurationReader
from haproxy.HaProxy import HaProxy


def load_haproxy_monitors(configuration):
    haproxy_monitors = {}
    # for name, url in configuration.get_haproxy_monitors().items():
    #     haproxy = HaProxy()
    #     haproxy.load_from_url(url)
    #     haproxy_monitors[name] = haproxy

    haproxy = HaProxy()
    haproxy.load_from_file("../../haproxy/example_haproxy_monitor.csv")
    haproxy_monitors['xxx'] = haproxy

    return haproxy_monitors


configuration_path = "sample_configuration.json"
configuration = ConfigurationReader.read(configuration_path)

haproxy_monitors = load_haproxy_monitors(configuration)

for cluster_name in configuration.get_clusters().keys():
    cluster_configuration = configuration.get_cluster(cluster_name)
    for hostdomain in cluster_configuration.get_hosts().keys():
        host_configuration = cluster_configuration.get_host(hostdomain)
