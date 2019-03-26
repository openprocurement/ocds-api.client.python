import logging
from time import time

from gevent import sleep

from ocds_client.exceptions import RequestFailed

LOGGER = logging.getLogger(__name__)


def get_response(client, params):
    response_fail = True
    sleep_interval = 0.2
    while response_fail:
        try:
            start = time()
            response = client.get_resource_items(params)
            end = time() - start
            LOGGER.debug(f'Request duration {end} sec', extra={'FEEDER_REQUEST_DURATION': end * 1000})
            response_fail = False
        except ConnectionError as e:
            LOGGER.error(f'ConnectionError: {repr(e)}', extra={'MESSAGE_ID': 'connection_error'})
            if sleep_interval > 300:
                raise e
            sleep_interval = sleep_interval * 2
            LOGGER.debug(f'Client sleeping after ConnectionError {sleep_interval} sec.')
            sleep(sleep_interval)
            continue
        except RequestFailed as e:
            LOGGER.error(f'RequestFailed: Status code: {e.status_code}', extra={'MESSAGE_ID': 'request_failed'})
            if e.status_code == 429:
                if sleep_interval > 120:
                    raise e
                LOGGER.debug(f'Client sleeping after RequestFailed {sleep_interval} sec.')
                sleep_interval = sleep_interval * 2
                sleep(sleep_interval)
                continue
            raise e
        except Exception as e:
            LOGGER.error(f'Exception: {repr(e)}', extra={'MESSAGE_ID': 'exceptions'})
            if sleep_interval > 300:
                raise e
            sleep_interval = sleep_interval * 2
            LOGGER.debug(f'Client sleeping after Exception: {repr(e)}, {sleep_interval} sec.')
            sleep(sleep_interval)
            continue
    return response
