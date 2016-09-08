import csv
from enum import Enum
from itertools import groupby
from urllib.request import urlopen


class Dict2Object:
    @classmethod
    def from_dict(cls, dictionary):
        return cls(**dictionary)


class Status(Enum):
    UP = "UP"
    DOWN = "DOWN"
    OPEN = "OPEN"

    @staticmethod
    def of(value):
        for name, member in Status.__members__.items():
            if name == value:
                return member
        raise Exception("Not found correct Status by value: %s" % value)


class Host(Dict2Object):
    def __init__(self, backend_name=None, name=None, current_sessions=0, max_sessions=0, backend=False,
                 status=Status.DOWN, last_status_change=0, downtime=0):
        # pxname
        self.backend_name = backend_name
        # svname
        self.name = name
        # scur
        self.current_sessions = current_sessions
        # smax
        self.max_sessions = max_sessions
        # bck
        self.backend = backend
        # status
        self.status = status
        # lastchg
        self.last_status_change = last_status_change
        # downtime
        self.downtime = downtime

    def __str__(self):
        return "HaProxyHost {" \
               "backend_name: " + str(self.backend_name) + ", " + \
               "name: " + str(self.name) + ", " + \
               "backend: " + str(self.backend) + ", " + \
               "status: " + str(self.status) + ", " + \
               "last_status_change: " + str(self.last_status_change) + ", " + \
               "downtime: " + str(self.downtime) + \
               "}"


class NotFoundHostException(Exception):
    pass


class HaProxy(Dict2Object):
    def __init__(self, monitor_data={}):
        self.monitor_data = monitor_data

    def get_backend_names(self):
        return self.monitor_data.keys()

    def get_hosts(self, backend_name):
        return self.monitor_data.get(backend_name)

    def get_available_hosts(self, backend_name):
        available_hosts = list()
        for host in self.get_hosts(backend_name):
            if host.status == Status.UP:
                available_hosts.append(host)
        return available_hosts

    def get_host(self, backend_name, host_name):
        for host in self.get_hosts(backend_name):
            if host.name == host_name:
                return Host.from_dict(host)
        raise NotFoundHostException("Not found host by name %s in backend name %s" % host_name, backend_name)

    def load_from_file(self, filename, skip_backend=True):
        with open(filename) as monitor:
            self.__load(monitor, skip_backend)

    def load_from_url(self, url, skip_backend=True):
        with urlopen(url) as monitor:
            self.__load(monitor.read().decode('utf-8').splitlines(), skip_backend)

    def __load(self, data, skip_backend):
        # print(type(data))
        reader = self.__csv_reader(data)
        pxname = reader.fieldnames[0]
        grouped = self.__group_by(reader, pxname)
        for backend_name, hosts in grouped:
            # print(backend_name)
            backend_name_hosts = list()
            for host_details in hosts:
                # print(host_details)
                host = Host()
                host.backend_name = backend_name
                host.name = host_details['svname']
                host.current_sessions = self.__to_int(host_details['scur'])
                host.max_sessions = self.__to_int(host_details['smax'])
                host.backend = self.__to_bool(host_details['bck'])
                host.status = Status.of(host_details['status'])
                host.last_status_change = self.__to_int(host_details['lastchg'])
                host.downtime = self.__to_int(host_details['downtime'])

                if skip_backend and host.backend:
                    pass
                else:
                    backend_name_hosts.append(host)

            self.monitor_data[backend_name] = backend_name_hosts

    def __csv_reader(self, data):
        return csv.DictReader(data)

    def __group_by(self, data, key):
        rows = sorted(data, key=lambda row: row[key])
        return groupby(rows, lambda row: row[key])

    def __to_int(self, data, default=0):
        try:
            return int(data)
        except ValueError:
            return default

    def __to_bool(self, data, default=False):
        if "0" == str(data):
            return False
        elif "1" == str(data):
            return True
        return default
