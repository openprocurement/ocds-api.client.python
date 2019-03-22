from requests import Session
from requests.auth import HTTPBasicAuth

from .exceptions import RequestFailed, http_exceptions_dict


class ClientTemplate:
    """Base class template for client"""

    def __init__(self, auth=None, headers=None):
        """
        Client template
            :param auth: tuple with login and password
            :param headers: dict with headers
        """

        self.headers = headers or {}
        self.session = Session()
        if auth is not None:
            self.session.auth = HTTPBasicAuth(*auth)

    def request(self, method, path=None, payload=None, json=None, headers=None, params_dict=None):
        _headers = self.headers.copy()
        _headers.update(headers or {})
        response = self.session.request(method, path, data=payload, json=json, headers=_headers, params=params_dict)

        if response.status_code >= 400:
            raise http_exceptions_dict.get(response.status_code, RequestFailed)(response)

        return response
