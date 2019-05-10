import json
import os

from .utils import Response
from gevent import spawn, sleep
from unittest.mock import patch

from ocds_client.sync import SyncClient

CWD = os.getcwd()


@patch('ocds_client.templates.Session')
def test_forward_worker(session):

    with open(f'{CWD}/ocds_client/tests/data/records-10.json', 'r') as f:
        data = f.read()
    session().request.return_value = Response(data, 200)

    host = 'http://localhost'
    resource = 'record'
    params = {'size': '10', 'ordering': 'desc'}
    retrievers_params = {
        'up_requests_sleep': 1,
        'up_wait_sleep': 1,
        'up_wait_sleep_min': 1,
        'queue_size': 101
    }
    sync_client = SyncClient(host, resource, params=params, retrievers_params=retrievers_params)

    def start_test_client():
        sync_client.init_client()
        for record in sync_client.get_resource_items():
            assert set(record.keys()) == {'ocid', 'compiledRelease', 'releases'}

    spawn(start_test_client)
    sleep(3)
    assert sync_client.backward_worker.ready() == False
    assert sync_client.backward_worker.exit_successful == False
    assert sync_client.forward_worker.ready() == False
    assert sync_client.forward_worker.exit_successful == False

    # emulate exception in backward worker, check restart_sync was called
    forward_worker = sync_client.forward_worker
    backward_worker = sync_client.backward_worker
    backward_worker.kill(exception=KeyError())
    sleep(3)
    assert sync_client.forward_worker != forward_worker  # restart_sync was called
    assert sync_client.backward_worker != backward_worker  # restart_sync was called
    assert forward_worker.exit_successful == False
    assert backward_worker.exit_successful == False
    assert forward_worker.ready() == True
    assert backward_worker.ready() == True

    # emulate exception in forward worker, check restart_sync was called
    forward_worker = sync_client.forward_worker
    backward_worker = sync_client.backward_worker
    forward_worker.kill(exception=KeyError())
    sleep(3)
    assert sync_client.forward_worker != forward_worker  # restart_sync was called
    assert sync_client.backward_worker != backward_worker  # restart_sync was called
    assert forward_worker.exit_successful == False
    assert backward_worker.exit_successful == False
    assert forward_worker.ready() == True
    assert backward_worker.ready() == True

    # emulate backward worker finished sync
    json_data = json.loads(data)
    json_data['records'] = []
    data = json.dumps(json_data)
    session().request.return_value = Response(data, 200)
    sleep(3)
    assert sync_client.backward_worker.ready() == True
    assert sync_client.backward_worker.exit_successful == True
    assert sync_client.forward_worker.ready() == False
    assert sync_client.forward_worker.exit_successful == False
