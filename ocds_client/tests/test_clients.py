import pytest
from ocds_client.clients import ResourceClient, RecordClient, ReleaseClient, BaseClient


def test_base_client_init():
    with pytest.raises(Exception) as e:
        BaseClient()
    assert e.value.args == ('Please provide OCDS API url.',)

    with pytest.raises(Exception) as e:
        BaseClient('http://localhost/')
    assert e.value.args == ('Please provide resource.',)

    host = 'https://localhost'
    resource = 'record'
    client = BaseClient(host, resource=resource)
    assert client.host_url == host
    assert client.resource == resource
    assert client.prefix_path == f'{host}/api'
    assert client.resource_param == 'ocid='

    resource = 'release'
    client = BaseClient(host, resource=resource)
    assert client.host_url == host
    assert client.resource == resource
    assert client.resource_param == 'releaseID='


def test_resource_client_get_resource_record(record_response):
    client = ResourceClient('https://localhost', resource='record')
    record_id = 'ocds-be6bcu-UA-2018-06-22-001789-a'
    record = client.get_resource_item(record_id)

    assert set(record.keys()) == {'releases', 'compiledRelease', 'ocid'}
    assert record.ocid == record_id


def test_resource_client_get_resource_release(release_response):
    client = ResourceClient('https://localhost', resource='release')
    release_id = 'c3f4965758c9b7391f86c676f59b828a'
    release = client.get_resource_item(release_id)
    assert set(release.keys()) == {'id',
                                   'tag',
                                   'date',
                                   'ocid',
                                   'buyer',
                                   'parties',
                                   'language',
                                   'contracts',
                                   'initiationType'}
    assert release.id == release_id


def test_resource_client_get_resorce_records(records_list_response):
    params = {'size': '10'}
    resource = 'record'
    host = 'https://localhost/'
    client = ResourceClient(host, resource=resource, params=params)

    assert client.params == params
    assert client.host_url == host
    assert client.resource == resource
    assert client.resource_param == 'ocid='

    response = client.get_resource_items()
    assert {'license',
            'publicationPolicy',
            'publishedDate',
            'records',
            'extensions',
            'links',
            'publisher',
            'version',
            'uri'} == set(response.keys())
    assert len(response.records) == 10
    assert 'page' in params
    assert params['size'] == '10'


def test_resource_client_get_resource_releases(releases_list_response):
    params = {'size': '10'}
    resource = 'releases'
    host = 'https://localhost/'
    client = ResourceClient(host, resource=resource, params=params)

    assert client.params == params
    assert client.host_url == host
    assert client.resource == resource
    assert client.resource_param == 'releaseID='

    response = client.get_resource_items()
    assert {'license',
            'publicationPolicy',
            'publishedDate',
            'releases',
            'extensions',
            'links',
            'publisher',
            'version',
            'uri'} == set(response.keys())
    assert len(response.releases) == 10
    assert 'page' in params
    assert params['size'] == '10'


def test_record_client_get_records(records_list_response):
    client = RecordClient('http://localhost')
    assert client.resource == 'record'

    records = client.get_records(params={'size': 10})
    assert len(records) == 10
    for record in records:
        assert set(record.keys()) == {'releases', 'compiledRelease', 'ocid'}


def test_record_client_get_record(record_response):
    client = RecordClient('http://localhost')
    record_id = 'ocds-be6bcu-UA-2018-06-22-001789-a'
    assert client.resource == 'record'

    record = client.get_record(record_id)
    assert set(record.keys()) == {'releases', 'compiledRelease', 'ocid'}
    assert record.ocid == record_id


def test_release_client_get_releases(releases_list_response):
    client = ReleaseClient('http://localhost')
    assert client.resource == 'release'

    releases = client.get_releases(params={'size': 10})
    assert len(releases) == 10
    for release in releases:
        assert set(release.keys()) == {'id',
                                       'tag',
                                       'date',
                                       'ocid',
                                       'buyer',
                                       'parties',
                                       'language',
                                       'contracts',
                                       'initiationType'}


def test_release_client_get_release(release_response):
    client = ReleaseClient('http://localhost')
    release_id = 'c3f4965758c9b7391f86c676f59b828a'
    assert client.resource == 'release'

    release = client.get_release(release_id)
    assert set(release.keys()) == {'id',
                                   'tag',
                                   'date',
                                   'ocid',
                                   'buyer',
                                   'parties',
                                   'language',
                                   'contracts',
                                   'initiationType'}
    assert release.id == release_id
