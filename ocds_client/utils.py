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
            LOGGER.debug('Request duration {} sec'.format(end), extra={'FEEDER_REQUEST_DURATION': end * 1000})
            response_fail = False
        except ConnectionError as e:
            LOGGER.error('ConnectionError: {}'.format(repr(e)), extra={'MESSAGE_ID': 'connection_error'})
            if sleep_interval > 300:
                raise e
            sleep_interval = sleep_interval * 2
            LOGGER.debug('Client sleeping after ConnectionError {} sec.'.format(sleep_interval))
            sleep(sleep_interval)
            continue
        except RequestFailed as e:
            LOGGER.error('RequestFailed: Status code: {}'.format(e.status_code),
                         extra={'MESSAGE_ID': 'request_failed'})
            if e.status_code == 429:
                if sleep_interval > 120:
                    raise e
                LOGGER.debug('Client sleeping after RequestFailed {} sec.'.format(sleep_interval))
                sleep_interval = sleep_interval * 2
                sleep(sleep_interval)
                continue
            raise e
        except Exception as e:
            LOGGER.error('Exception: {}'.format(repr(e)), extra={'MESSAGE_ID': 'exceptions'})
            if sleep_interval > 300:
                raise e
            sleep_interval = sleep_interval * 2
            LOGGER.debug('Client sleeping after Exception: {}, {} sec.'.format(repr(e), sleep_interval))
            sleep(sleep_interval)
            continue
    return response
