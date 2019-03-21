import os

import pytest
from .utils import Response

CWD = os.getcwd()


@pytest.fixture
def records_list_response(mocker):
    res = mocker.patch('ocds_client.templates.Session')
    with open(f'{CWD}/ocds_client/tests/data/records-10.json', 'r') as f:
        data = f.read()
    res().request.return_value = Response(data, 200)


@pytest.fixture
def releases_list_response(mocker):
    res = mocker.patch('ocds_client.templates.Session')
    with open(f'{CWD}/ocds_client/tests/data/releases-10.json', 'r') as f:
        data = f.read()
    res().request.return_value = Response(data, 200)


@pytest.fixture
def record_response(mocker):
    res = mocker.patch('ocds_client.templates.Session')
    with open(f'{CWD}/ocds_client/tests/data/record-ocds-be6bcu-UA-2018-06-22-001789-a.json', 'r') as f:
        data = f.read()
    res().request.return_value = Response(data, 200)


@pytest.fixture
def release_response(mocker):
    res = mocker.patch('ocds_client.templates.Session')
    with open(f'{CWD}/ocds_client/tests/data/release-c3f4965758c9b7391f86c676f59b828a.json', 'r') as f:
        data = f.read()
    res().request.return_value = Response(data, 200)
