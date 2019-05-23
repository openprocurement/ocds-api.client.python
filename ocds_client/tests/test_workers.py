import json
import os

from .utils import Response
from gevent import spawn, sleep
from unittest import TestCase
from unittest.mock import patch, MagicMock

from ocds_client.sync import SyncClient

CWD = os.getcwd()


class TestWorkers(TestCase):
    host = 'http://localhost'
    resource = 'record'
    params = {'size': '10', 'ordering': 'desc'}
    retrievers_params = {
        'up_requests_sleep': 1,
        'up_wait_sleep': 1,
        'up_wait_sleep_min': 1,
        'queue_size': 101
    }

    @classmethod
    def setUpClass(cls):
        with open(f'{CWD}/ocds_client/tests/data/records-10.json', 'r') as f:
            cls.data = f.read()

    def setUp(self):
        self.sync_client = SyncClient(self.host, self.resource, params=self.params,
                                      retrievers_params=self.retrievers_params)

    @staticmethod
    def start_test_client(sync_client):
        sync_client.init_clients()
        for record in sync_client.get_resource_items():
            assert set(record.keys()) == {'ocid', 'compiledRelease', 'releases'}

    @patch('ocds_client.templates.Session')
    def test_forward_worker(self, session):

        session().request.return_value = Response(self.data, 200)

        spawn(self.start_test_client, self.sync_client)
        sleep(3)
        self.assertEqual(self.sync_client.backward_worker.ready(), False)
        self.assertEqual(self.sync_client.backward_worker.exit_successful, False)
        self.assertEqual(self.sync_client.forward_worker.ready(), False)
        self.assertEqual(self.sync_client.forward_worker.exit_successful, False)

        # emulate backward worker finished sync
        json_data = json.loads(self.data)
        json_data['records'] = []

        data_without_records = json.dumps(json_data)
        session().request.return_value = Response(data_without_records, 200)
        sleep(3)
        self.assertEqual(self.sync_client.backward_worker.ready(), True)
        self.assertEqual(self.sync_client.backward_worker.exit_successful, True)
        self.assertEqual(self.sync_client.forward_worker.ready(), False)
        self.assertEqual(self.sync_client.forward_worker.exit_successful, False)

    @patch('ocds_client.templates.Session')
    def test_workers_with_backward_exception(self, session):

        session().request.return_value = Response(self.data, 200)

        # start sync
        spawn(self.start_test_client, self.sync_client)
        sleep(3)
        self.assertEqual(self.sync_client.backward_worker.ready(), False)
        self.assertEqual(self.sync_client.backward_worker.exit_successful, False)
        self.assertEqual(self.sync_client.forward_worker.ready(), False)
        self.assertEqual(self.sync_client.forward_worker.exit_successful, False)

        restart_sync_mock = MagicMock(return_value='weird value')
        self.sync_client.restart_sync = restart_sync_mock

        # emulate exception in backward worker, check restart_sync was called
        backward_worker = self.sync_client.backward_worker
        backward_worker.kill(exception=KeyError())
        sleep(3)
        self.sync_client.restart_sync.assert_called_with()

    @patch('ocds_client.templates.Session')
    def test_workers_with_forward_exception(self, session):

        session().request.return_value = Response(self.data, 200)
        spawn(self.start_test_client, self.sync_client)

        sleep(3)
        self.assertEqual(self.sync_client.backward_worker.ready(), False)
        self.assertEqual(self.sync_client.backward_worker.exit_successful, False)
        self.assertEqual(self.sync_client.forward_worker.ready(), False)
        self.assertEqual(self.sync_client.forward_worker.exit_successful, False)

        restart_sync_mock = MagicMock(return_value='weird value')
        self.sync_client.restart_sync = restart_sync_mock

        # emulate exception in forward worker, check restart_sync was called
        forward_worker = self.sync_client.forward_worker
        forward_worker.kill(exception=KeyError())
        sleep(3)
        self.sync_client.restart_sync.assert_called_with()
