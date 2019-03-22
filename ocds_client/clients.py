import logging

import backoff
from munch import munchify
from simplejson import loads

from ocds_client.templates import ClientTemplate
from ocds_client.exceptions import InvalidResponse, RequestFailed
from urllib import parse

LOGGER = logging.getLogger(__name__)


class BaseClient(ClientTemplate):
    """Base client for OCDS"""
    resource = ''

    def __init__(self, host_url='', resource=None, params={}, auth=None, headers=None):
        if not host_url:
            raise Exception('Please provide OCDS API url.')
        super().__init__(auth=auth, headers=headers)
        self.params = params
        self.host_url = host_url
        self.resource = resource or self.resource
        if not self.resource:
            raise Exception('Please provide resource.')
        self.resource_param = 'ocid=' if self.resource == 'record' else 'releaseID='
        self.prefix_path = f'{self.host_url}/api'

    @backoff.on_exception(backoff.expo, RequestFailed, max_tries=5)
    def _get_resource_item(self, url, headers=None):
        _headers = self.headers.copy()
        _headers.update(headers or {})
        response_item = self.request('GET', url, headers=_headers)
        if response_item.status_code == 200:
            return munchify(loads(response_item.text))
        raise InvalidResponse(response_item)

    @backoff.on_exception(backoff.expo, RequestFailed, max_tries=5)
    def _get_resource_items(self, params=None):
        _params = (params or {}).copy()
        self.params.update(_params)
        response = self.request('GET', f'{self.prefix_path}/{self.resource}s.json', params_dict=self.params)
        response_data = munchify(loads(response.text))
        _params = {k: v[0]
                   for k, v in parse.parse_qs(parse.urlparse(response_data.links.next).query).items()}
        self.params.update(_params)
        return response_data


class ResourceClient(BaseClient):

    def get_resource_item(self, resource_id, headers=None):
        _headers = self.headers.copy()
        _headers.update(headers or {})
        param = f'{self.resource_param}{resource_id}'
        url = f'{self.prefix_path}/{self.resource}.json?{param}'
        data = self._get_resource_item(url, headers=headers)
        return data[f'{self.resource}s'][0]

    def get_resource_items(self, params=None):
        return self._get_resource_items(params)


class RecordClient(ResourceClient):
    resource = 'record'

    def get_record(self, record_id, headers=None):
        return self.get_resource_item(resource_id=record_id, headers=headers)

    def get_records(self, params=None):
        return self.get_resource_items(params=params)[f'{self.resource}s']


class ReleaseClient(ResourceClient):
    resource = 'release'

    def get_release(self, release_id, headers=None):
        return self.get_resource_item(resource_id=release_id, headers=headers)

    def get_releases(self, params):
        return self.get_resource_items(params)[f'{self.resource}s']
