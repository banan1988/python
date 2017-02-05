import re
from urllib.parse import urlparse

__all__ = ["Validator"]

__version__ = "0.1"


class Validator:
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
