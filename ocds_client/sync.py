import gevent.monkey
gevent.monkey.patch_all()

import logging
from urllib import parse
from gevent import idle, spawn, sleep
from gevent.queue import Queue, Empty
from ocds_client.clients import ResourceClient
from ocds_client.utils import get_response
from time import time

LOGGER = logging.getLogger(__name__)
DEFAULT_FORWARD_HEARTBEAT = 54000
DEFAULT_RETRIEVERS_PARAMS = {
    'up_requests_sleep': 1,
    'up_wait_sleep': 30,
    'up_wait_sleep_min': 5,
    'queue_size': 101
}


class SyncClient:
    idle = idle

    def __init__(self,
                 host_url,
                 resource,
                 auth=None,
                 params={},
                 headers=None,
                 retrievers_params=DEFAULT_RETRIEVERS_PARAMS,
                 adaptive=False,
                 with_priority=False):
        LOGGER.info('Init SyncClient for resource {resource}')
        self.host = host_url
        self.auth = auth
        self.resource = resource
        self.adaptive = adaptive
        self.headers = headers

        self.params = params
        self.retrievers_params = retrievers_params
        self.queue = Queue(maxsize=retrievers_params['queue_size'])

    def init_client(self):
        self.client = ResourceClient(self.host, self.resource, self.params, self.auth, self.headers)

    def handle_response_data(self, data):
        for resource_item in data:
            self.queue.put(resource_item)

    def worker_watcher(self):
        while True:
            if time() - self.heartbeat > DEFAULT_FORWARD_HEARTBEAT:
                self.restart_sync()
                LOGGER.warning('Restart sync, reason: Last response from forward greater than 15 min ago.')
            sleep(300)

    def start_sync(self):
        LOGGER.info('Start sync...')

        data = self.client.get_resource_items(self.params)

        self.handle_response_data(data[f'{self.resource}s'])
        params = {k: v[0] for k, v in parse.parse_qs(parse.urlparse(data.links.next).query).items()}
        self.params.update(params)
        self.worker = spawn(self.retriever)
        self.heartbeat = time()
        self.watcher = spawn(self.worker_watcher)

    def restart_sync(self):
        """
        Restart retrieving from OCDS API.
        """

        LOGGER.info('Restart worker')
        self.worker.kill()
        self.watcher.kill()
        self.init_client()
        self.start_sync()

    def get_resource_items(self):
        self.init_client()
        self.start_sync()
        while True:
            if self.worker.ready():
                self.restart_sync()
            while not self.queue.empty():
                LOGGER.debug('Sync queue size: {}'.format(self.queue.qsize()),
                             extra={'SYNC_QUEUE_SIZE': self.queue.qsize()})
                LOGGER.debug('Yield resource item', extra={'MESSAGE_ID': 'sync_yield'})
                yield self.queue.get()
            LOGGER.debug('Sync queue size: {}'.format(self.queue.qsize()),
                         extra={'SYNC_QUEUE_SIZE': self.queue.qsize()})
            try:
                self.queue.peek(block=True, timeout=0.1)
            except Empty:
                pass

    def log_state(self):
        LOGGER.debug(f'Retriever params state: {self.params}')
        print(f'STATE: {self.params}')

    def retriever(self):
        LOGGER.info('Retriever: Start job...')
        response = get_response(self.client, self.params)
        LOGGER.debug('Retriever response length {} items'.format(len(response[f'{self.resource}s'])),
                     extra={'RETRIEVER_RESPONSE_LENGTH': len(response[f'{self.resource}s'])})
        while True:
            self.heartbeat = time()
            while (response[f'{self.resource}s']):
                self.heartbeat = time()
                self.handle_response_data(response[f'{self.resource}s'])
                params = {k: v[0] for k, v in parse.parse_qs(parse.urlparse(response.links.next).query).items()}
                self.params.update(params)
                self.log_state()
                response = get_response(self.client, self.params)
                LOGGER.debug('Retriever response length {} items'.format(len(response[f'{self.resource}s'])),
                             extra={'RETRIEVER_RESPONSE_LENGTH': len(response[f'{self.resource}s'])})
                if len(response[f'{self.resource}s']) != 0:
                    LOGGER.info('Retriever: pause between requests {} sec.'.format(
                        self.retrievers_params.get('up_requests_sleep', 5.0)))
                    sleep(self.retrievers_params.get('up_requests_sleep', 5.0))
            LOGGER.info('Retriever: pause after empty response {} sec.'.format(
                self.retrievers_params.get('up_wait_sleep', 30.0)),
                extra={'RETRIEVER_WAIT_SLEEP': self.retrievers_params.get('up_wait_sleep', 30.0)})
            sleep(self.retrievers_params.get('up_wait_sleep', 30.0))
            response = get_response(self.client, self.params)
            LOGGER.debug('Retriever response length {} items'.format(len(response[f'{self.resource}s'])),
                         extra={'RETRIEVER_RESPONSE_LENGTH': len(response[f'{self.resource}s'])})
            if self.adaptive:
                if len(response.data) != 0:
                    if (self.retrievers_params['up_wait_sleep'] > self.retrievers_params['up_wait_sleep_min']):
                        self.retrievers_params['up_wait_sleep'] -= 1
                else:
                    if self.retrievers_params['up_wait_sleep'] < 30:
                        self.retrievers_params['up_wait_sleep'] += 1
        return 1
