import gevent.monkey
gevent.monkey.patch_all()

import logging
from gevent import Greenlet, sleep
from time import time
from urllib import parse

from ocds_client.utils import get_response, PrioritizedItem


LOGGER = logging.getLogger(__name__)


class BaseWorker(Greenlet):

    def __init__(self, sync_client, client, params):
        Greenlet.__init__(self)
        self.sync_client = sync_client
        self.resource = self.sync_client.resource
        self.retrievers_params = self.sync_client.retrievers_params
        self.adaptive = self.sync_client.adaptive
        self.client = sync_client.forward_client
        self.params = params
        self.exit_successful = False
        self.queue_priority = 1

    def log_state(self):
        LOGGER.debug(f'{self.name} params state: {self.params}')

    def handle_response_data(self, data):
        for resource_item in data:
            self.sync_client.queue.put(PrioritizedItem(self.queue_priority, resource_item))

    def _run(self):
        LOGGER.info(f'{self.name}: Start job...')
        response = get_response(self.client, self.params)
        records_len = len(response[f'{self.resource}s'])
        LOGGER.debug(f'Retriever response length {records_len} items',
                     extra={f'{self.name.upper()}_RESPONSE_LENGTH': records_len})
        while not self.exit_successful:
            self.sync_client.heartbeat = time()
            while (response[f'{self.resource}s']):
                self.sync_client.heartbeat = time()
                self.handle_response_data(response[f'{self.resource}s'])
                params = {k: v[0] for k, v in parse.parse_qs(parse.urlparse(response.links.next).query).items()}
                self.params.update(params)
                self.log_state()
                response = get_response(self.client, self.params)
                records_len = len(response[f'{self.resource}s'])
                LOGGER.debug(f'{self.name} response length {records_len} items',
                             extra={f'{self.name.upper()}_RESPONSE_LENGTH': records_len})
                if records_len != 0:
                    timeout = self.retrievers_params.get('up_requests_sleep', 5.0)
                    LOGGER.info(f'{self.name}: pause between requests {timeout} sec.')
                    sleep(timeout)
            if self.name == 'BackwardWorker':
                self.exit_successful = True
            up_wait_sleep = self.retrievers_params.get('up_wait_sleep', 30.0)
            LOGGER.info(f'{self.name}: pause after empty response {up_wait_sleep} sec.',
                        extra={f'{self.name}_WAIT_SLEEP': up_wait_sleep})
            sleep(up_wait_sleep)
            response = get_response(self.client, self.params)
            records_len = len(response[f'{self.resource}s'])
            LOGGER.debug(f'{self.name} response length {records_len} items',
                         extra={f'{self.name.upper()}_RESPONSE_LENGTH': records_len})
            if self.adaptive:
                if len(response[f'{self.resource}s']) != 0:
                    if self.retrievers_params['up_wait_sleep'] > self.retrievers_params['up_wait_sleep_min']:
                        self.retrievers_params['up_wait_sleep'] -= 1
                else:
                    if self.retrievers_params['up_wait_sleep'] < 30:
                        self.retrievers_params['up_wait_sleep'] += 1
        return 1

    def __str__(self):
        return f'{self.name} greenlet'


class ForwardWorker(BaseWorker):

    def __init__(self, sync_client, client, params):
        super().__init__(sync_client, client, params)
        self.name = 'ForwardWorker'
        self.queue_priority = 1
        self.client = sync_client.forward_client

    def check(self):
        return self.ready()


class BackwardWorker(BaseWorker):

    def __init__(self, sync_client, client, params):
        super().__init__(sync_client, client, params)
        self.name = 'BackwardWorker'
        self.exit_successful = False
        self.queue_priority = 1000
        self.client = sync_client.backward_client

    def check(self):
        if not self.exit_successful:
            return self.ready()
        return False
