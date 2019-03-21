import pytest
from ocds_client.utils import get_response
from .utils import Response
from ocds_client.exceptions import RequestFailed
from requests.exceptions import InvalidHeader


def test_success_response(mocker):
    client = mocker.MagicMock()
    data = [{'ocid': 'ocid_id', 'compiledRelease': {'ocid': 'ocid'}, 'releases': ['release_link']}]
    client.get_resource_items.return_value = data
    response = get_response(client, {})
    assert response == data


def test_connection_error_response(mocker):
    client = mocker.MagicMock()
    mocker.patch('ocds_client.utils.sleep')
    client.get_resource_items.side_effect = ConnectionError('ConnectionError')
    with pytest.raises(ConnectionError) as e:
        get_response(client, {})
    assert e.value.args == ('ConnectionError',)


def test_request_failed_response(mocker):
    client = mocker.MagicMock()
    mocker.patch('ocds_client.utils.sleep')
    response = Response('{"error": "Too many requests."}', 429)
    client.get_resource_items.side_effect = RequestFailed(response)
    with pytest.raises(RequestFailed) as e:
        get_response(client, {})
    assert e.value.message == '{"error": "Too many requests."}'
    assert e.value.status_code == 429

    response = Response('{"error": "Internal Server Error."}', 500)
    client.get_resource_items.side_effect = RequestFailed(response)
    with pytest.raises(RequestFailed) as e:
        get_response(client, {})
    assert e.value.message == '{"error": "Internal Server Error."}'
    assert e.value.status_code == 500


def test_exception_response(mocker):
    client = mocker.MagicMock()
    mocker.patch('ocds_client.utils.sleep')
    client.get_resource_items.side_effect = InvalidHeader('Missing X-Token')

    with pytest.raises(InvalidHeader) as e:
        get_response(client, {})
    assert e.value.args == ('Missing X-Token',)
