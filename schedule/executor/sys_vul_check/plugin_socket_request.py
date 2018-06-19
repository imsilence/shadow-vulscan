#encoding: utf-8

import socket
import logging
import traceback

TYPE = 'socket_request'

DEFAULT_TIMEOUT = 5
DEFAULT_PORT = 80
DEFAULT_TEXT = 'shadow'
DEFAULT_SIZE = 1024

logger = logging.getLogger(__name__)

def run(job_params, plugin_info, plugin_config, *args, **kwargs):
    ip = job_params.get('ip', '')

    flag, payloads = check(ip, plugin_config)

    if flag:
        yield ip, {
            ident : {
                'payloads' : payloads
            }
        }

    yield ip, None


def check(ip, plugin_config):
    timeout = int(plugin_config.get('timeout', DEFAULT_TIMEOUT))
    port = int(plugin_config.get('port', DEFAULT_PORT))
    request = str(plugin_config.get('request', DEFAULT_REQUEST)).encode()
    size = int(plugin_config.get('size', DEFAULT_SIZE))
    flag = str(plugin_config.get('flag', '')).lower()

    try:
        socket.setdefaulttimeout(timeout)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((ip, port))
        client.send(text)
        response = client.recv(size)
        response = response.decode().lower()

        pos = response.find(flag)
        if pos != -1:
            length = len(text)
            start = pos - 20
            end = pos + len(value) + 20
            start = 0 if start < 0 else start
            end = length if end > length else end

            return True, {'response' : response[start, end]}
    except BaseException as e:
        logger.exception(e)
        logger.error(e)

    return False, None
