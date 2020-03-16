import concurrent.futures
import json
import os
import random
import sys
import urllib.request

post_resources = ["/post"]
post_data = [
    {"value": "hello"},
    {"value": "good bye"},
    {"value": "hi"}
]

resources = ["/slow", "/fast"]
resources_query_parameter = ["/fast?queryParameter=abc", "/fast?queryParameter=xyz"]
monitoring_resources = ["/monitoring/gustavo", "/monitoring/ivan", "/monitoring/joshua"]


class ELKRequest:
    def __init__(self, url, data=None):
        self.url = url
        self.data = data

    def __str__(self):
        return "ELKRequest {" \
               "url: " + str(self.url) + ", " + \
               "data: " + str(self.data) + \
               "}"


def send_post(request, timeout):
    params = json.dumps(request.data).encode('utf8')
    req = urllib.request.Request(request.url,
                                 data=params,
                                 headers={'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as connection:
        return connection.read()


def execute(request, timeout):
    if request.data:
        return send_post(request, timeout)
    with urllib.request.urlopen(request.url, timeout=timeout) as connection:
        return connection.read()


def send(requests, workers=10, timeout=60):
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        count = 1
        future_to_url = {executor.submit(execute, request, timeout): request for request in requests}
        for future in concurrent.futures.as_completed(future_to_url):
            request = future_to_url[future]
            try:
                data = future.result()
            except Exception as exc:
                print('%s generated an exception: %s' % (request, exc))
            else:
                print('%s page is %d bytes' % (request, len(data)))
            finally:
                print('done %d/%d' % (count, len(requests)))
                count += 1


def generate_urls(host, resources, limit=100):
    URLs = []
    for i in range(limit):
        choice = random.randint(0, len(resources) - 1)
        url = "http://" + host + resources[choice]
        URLs.append(ELKRequest(url))
    return URLs


def generate_data_urls(host, resources, datas, limit=100):
    URLs = []
    for i in range(limit):
        choice = random.randint(0, len(resources) - 1)
        url = "http://" + host + resources[choice]
        data_choice = random.randint(0, len(datas) - 1)
        data = datas[data_choice]
        URLs.append(ELKRequest(url, data))
    return URLs


def main():
    host = get_host()

    post_urls = generate_data_urls(host, post_resources, post_data, 50)
    resources_urls = generate_urls(host, resources, 200)
    resources_query_parameter_urls = generate_urls(host, resources_query_parameter, 50)
    monitoring_resources_urls = generate_urls(host, monitoring_resources)
    urls = post_urls + resources_urls + resources_query_parameter_urls + monitoring_resources_urls
    random.shuffle(urls)

    send(urls)


def get_host():
    if len(sys.argv) == 2:
        return sys.argv[1]

    raise Exception("Pass HOSTNAME:PORT as a parameter.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
