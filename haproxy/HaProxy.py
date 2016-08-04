import csv
from enum import Enum
from itertools import groupby
from urllib.request import urlopen


def to_int(data, default=0):
    try:
        return int(data)
    except ValueError:
        return default


def to_minutes(seconds):
    return int(seconds / 60)


class Status(Enum):
    UP = "UP"
    DOWN = "DOWN"

    @staticmethod
    def of(value):
        for val in Status:
            if val == value:
                return val
        raise Exception("Not found correct Status by value: %s" % value)


class HaProxyHost:
    # pxname
    group = None
    # svname
    name = None
    # scur
    current_sessions = 0
    # smax
    max_sessions = 0
    # bck
    backend = False
    # status
    status = Status.DOWN
    # lastchg
    last_status_change = 0
    # downtime
    downtime = 0


filename = "example_haproxy_monitor.csv"
url = "http://localhost:8000/sync_monitor;csv;norefresh"


class HaProxy:
    groups = dict()

    def __csv_reader(self, data):
        return csv.DictReader(data)

    def __group_by(self, data, key):
        rows = sorted(data, key=lambda row: row[key])
        return groupby(rows, lambda row: row[key])

    def load_from_file(self, filename):
        with open(filename) as monitor:
            print(type(monitor))
            reader = self.__csv_reader(monitor)
            pxname = reader.fieldnames[0]
            grouped = self.__group_by(reader, pxname)
            for group, hosts in grouped:
                print(group)
                for host_details in hosts:
                    print(host_details)
                    host = HaProxyHost()
                    host.group = group
                    host.name = host_details['svname']
                    host.current_sessions = host_details['scur']
                    host.max_sessions = host_details['smax']
                    host.backend = host_details['bck']
                    host.status = host_details['status']
                    host.last_status_change = host_details['lastchg']
                    host.downtime = host_details['downtime']

    def load_from_url(self, url):
        with urlopen(url) as monitor:
            print(type(monitor))
            reader = self.__csv_reader(monitor.read().decode('utf-8').splitlines())
            pxname = reader.fieldnames[0]
            grouped = self.__group_by(reader, pxname)


haproxy = HaProxy()
haproxy.load_from_file(filename)
haproxy.load_from_url(url)
