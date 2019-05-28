import gevent.monkey
gevent.monkey.patch_all()

import logging
from copy import deepcopy
from urllib import parse
from gevent import idle, spawn, sleep
from gevent.queue import PriorityQueue, Empty
from ocds_client.utils import PrioritizedItem
from ocds_client.clients import ResourceClient
from ocds_client.workers import ForwardWorker, BackwardWorker
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
    backward_class = BackwardWorker
    forward_class = ForwardWorker

    def __init__(self,
                 host_url,
                 resource,
                 auth=None,
                 params={},
                 headers=None,
                 retrievers_params=DEFAULT_RETRIEVERS_PARAMS,
                 adaptive=False,
                 with_priority=False):
        LOGGER.info(f'Init SyncClient for resource {resource}')
        self.host = host_url
        self.auth = auth
        self.resource = resource
        self.adaptive = adaptive
        self.headers = headers

        self.params = params
        self.retrievers_params = retrievers_params
        self.queue = PriorityQueue(maxsize=retrievers_params['queue_size'])

    def init_clients(self):
        self.backward_client = ResourceClient(self.host, self.resource, self.params, self.auth, self.headers)
        self.forward_client = ResourceClient(self.host, self.resource, self.params, self.auth, self.headers)

    def handle_response_data(self, data):
        for resource_item in data:
            self.queue.put(PrioritizedItem(1, resource_item))

    def worker_watcher(self):
        while True:
            if time() - self.heartbeat > DEFAULT_FORWARD_HEARTBEAT:
                self.restart_sync()
                LOGGER.warning('Restart sync, reason: Last response from workers greater than 15 min ago.')
            sleep(300)

    def start_sync(self):
        LOGGER.info('Start sync...')

        data = self.backward_client.get_resource_items(self.params)

        self.handle_response_data(data[f'{self.resource}s'])

        forward_params = deepcopy(self.params)
        forward_params.update({k: v[0] for k, v in parse.parse_qs(parse.urlparse(data.links.prev).query).items()})
        backward_params = deepcopy(self.params)
        backward_params.update({k: v[0] for k, v in parse.parse_qs(parse.urlparse(data.links.next).query).items()})

        self.forward_worker = self.forward_class(sync_client=self, client=self.forward_client, params=forward_params)
        self.backward_worker = self.backward_class(sync_client=self, client=self.backward_client,
                                                   params=backward_params)
        self.workers = [self.forward_worker, self.backward_worker]

        for worker in self.workers:
            worker.start()
        self.heartbeat = time()
        self.watcher = spawn(self.worker_watcher)

    def restart_sync(self):
        """
        Restart retrieving from OCDS API.
        """

        LOGGER.info('Restart workers')
        for worker in self.workers:
            worker.kill()
        self.watcher.kill()
        self.init_clients()
        self.start_sync()

    def get_resource_items(self):
        self.init_clients()
        self.start_sync()
        while True:
            if self.forward_worker.check() or self.backward_worker.check():
                self.restart_sync()
            while not self.queue.empty():
                LOGGER.debug(f'Sync queue size: {self.queue.qsize()}', extra={'SYNC_QUEUE_SIZE': self.queue.qsize()})
                LOGGER.debug('Yield resource item', extra={'MESSAGE_ID': 'sync_yield'})
                item = self.queue.get()
                yield item.data
            LOGGER.debug(f'Sync queue size: {self.queue.qsize()}', extra={'SYNC_QUEUE_SIZE': self.queue.qsize()})
            try:
                self.queue.peek(block=True, timeout=0.1)
            except Empty:
                pass
