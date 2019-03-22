import pytest
from requests import Session
from requests.auth import HTTPBasicAuth

from ocds_client.exceptions import Forbidden, RequestFailed
from ocds_client.templates import ClientTemplate

from .utils import Response


def test_client_template_init():
    template = ClientTemplate()
    assert template.headers == {}
    assert isinstance(template.session, Session)
    assert template.session.auth is None

    headers = {'MFA-Token': 'V3ry s3cr3t t0k3n'}
    auth = ('username', 'password')
    template = ClientTemplate(auth, headers)
    assert template.headers == headers
    assert template.session.auth == HTTPBasicAuth(*auth)


def test_request_exceptions(mocker):
    session = mocker.patch('ocds_client.templates.Session')
    data = '{"error": "Access Denied"}'
    response = Response(data, 403)
    session().request.return_value = response
    template = ClientTemplate()
    with pytest.raises(Forbidden) as e:
        template.request('GET', 'https://localhost/api/records.json')
    assert isinstance(e.value, Forbidden)
    assert e.value.message == data
    assert e.value.status_code == 403

    data = '{"error": "Internal Server Error"}'
    response = Response(data, 500)
    session().request.return_value = response
    with pytest.raises(RequestFailed) as e:
        template.request('GET', 'https://localhost/api/1.0/releases.json')
    assert isinstance(e.value, RequestFailed)
    assert e.value.message == data
    assert e.value.status_code == 500
