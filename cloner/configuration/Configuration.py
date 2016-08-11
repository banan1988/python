class ConfiguratonItem:
    source_hosts = list()
    target_hosts = list()
    traffic_rate = '100%'
    listen_port = 8080
    allow_url_regexp = None
    disallow_url_regexp = None
    rewrite_url = None
    save_responses = False
    http_timeout = '120s'


class Cluster:
    name = None
    always_running = False
    haproxy_monitor = None
    haproxy_backend_name = None
    configuration_items = list()
