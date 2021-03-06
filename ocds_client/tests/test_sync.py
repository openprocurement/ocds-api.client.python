def test_handle_response_data(records_list_response, sync_client):
    assert sync_client.resource == 'record'
    assert sync_client.queue.qsize() == 0

    sync_client.init_clients()
    data = sync_client.backward_client.get_resource_items()
    sync_client.handle_response_data(data.records)
    assert sync_client.queue.qsize() == 10
    record = sync_client.queue.get()
    assert set(record.data.keys()) == {'ocid', 'compiledRelease', 'releases'}


def test_start_sync(sync_client, mocker, records_list_response):
    spawn = mocker.patch('ocds_client.sync.spawn')
    time = mocker.patch('ocds_client.sync.time')
    time.return_value = 1
    assert 'page' not in sync_client.params
    assert not hasattr(sync_client, 'heartbeat')
    assert not hasattr(sync_client, 'worker')
    assert not hasattr(sync_client, 'watcher')

    sync_client.init_clients()
    sync_client.start_sync()
    assert 'page' in sync_client.params
    assert hasattr(sync_client, 'heartbeat')
    assert hasattr(sync_client, 'workers')
    assert hasattr(sync_client, 'watcher')
    assert sync_client.heartbeat == 1
    assert [mocker.call(sync_client.worker_watcher)] == spawn.call_args_list


def test_restart_sync(sync_client, mocker, records_list_response):
    mocker.patch('ocds_client.sync.spawn')
    assert not hasattr(sync_client, 'heartbeat')
    assert not hasattr(sync_client, 'worker')
    assert not hasattr(sync_client, 'watcher')

    sync_client.init_clients()
    sync_client.start_sync()
    workers = sync_client.workers
    sync_client.restart_sync()
    assert sync_client.workers != workers
    assert sync_client.watcher.kill.called
