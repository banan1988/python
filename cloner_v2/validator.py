import re
from urllib.parse import urlparse

__all__ = ["Validator"]

__version__ = "0.1"


class Validator:
    @staticmethod
    def is_hostname(hostname):
        if len(hostname) > 255:
            return False
        if hostname[-1] == ".":
            hostname = hostname[:-1]  # strip exactly one dot from the right, if present
        allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
        return all(allowed.match(x) for x in hostname.split("."))

    @staticmethod
    def is_url(url):
        parsed_url = urlparse(url)
        return parsed_url.scheme in ["ftp", "http", "https"]

    @staticmethod
    def is_url_path(path):
        parsed_path = urlparse(path)
        return parsed_path.path and parsed_path.path.startswith("/")

    @staticmethod
    def is_regexp(regexp):
        try:
            re.compile(regexp)
            return True
        except re.error:
            return False

    @staticmethod
    def is_rewrite_path(rewrite_path):
        parts = rewrite_path.split(":")
        if len(parts) == 2:
            return Validator.is_regexp(parts[0])
        return False
