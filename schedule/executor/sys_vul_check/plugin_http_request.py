#encoding: utf-8
import requests
import logging
import traceback

TYPE = 'http_request'

DEFAULT_PORTS = {
    'http' : 80,
    'https' : 443
}

DEFAULT_TIMEOUT = 5

logger = logging.getLogger(__name__)

def run(job_params, plugin_info, plugin_config, *args, **kwargs):
    ident = plugin_info.ident

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
    protocol = plugin_config.get('protocol', 'http')
    port = plugin_config.get('port', DEFAULT_PORTS.get(protocol))
    path = plugin_config.get('path', '/')
    url = '{protocol}://{host}:{port}/{path}'.format(protocol=protocol, host=ip, port=port, path=path.lstrip('/'))
    method = plugin_config.get('method', 'GET').lower()
    cookies = plugin_config.get('cookies', {})
    args = plugin_config.get('args', {})
    body = plugin_config.get('body', {})
    headers = plugin_config.get('headers', {})
    flags = plugin_config.get('flags', {})
    timeout = plugin_config.get('timeout', DEFAULT_TIMEOUT)

    if args:
        url = '{url}?{args}'.format(url, urllib.parse.urlencode(args))

    func = getattr(requests, method, 'get')
    try:
        response = func(url, body, headers=headers, cookies=cookies, timeout=timeout, verify=False)
        check_response = 'check_{0}'.format(flags.get('type', 'status_code'))
        func = globals().get(check_response, None)
        if func is None:
            logger.error('check response func not found: %s', check_response)
            return False, None

        return func(response, flags)
    except BaseException as e:
        logger.exception(e)
        logger.error(traceback.format_exc())
        return False, None


def check_status_code(response, flags):
    status_code = flags.get('status_code', [])
    if not isinstance(status_code, (tuple, list)):
        status_code = [status_code]

    logger.debug('check status code:%s, %s', status_code, response.status_code)
    if response.status_code in status_code:
        return True, {'status_code' : status_code}

    return False, None


def check_header(response, flags):
    header = str(flags.get('header', '')).lower()
    key = str(flags.get('key', '')).lower()
    value = str(flags.get('value', '')).lower()

    logger.debug('check header:%s, %s, %s', header, value, response.headers)
    for k, v in response.headers.items():
        if k.lower() == key:
            return value in v.lower(), {'header' : k, 'value' : v}

    return False, None


def check_response_body(response, flags):
    value = str(flags.get('body', '')).lower()
    text = response.text.lower()
    pos = text.find(value)
    logger.debug('check response_body:%s, %s', value, text)
    if pos != -1:
        length = len(text)
        start = pos - 20
        end = pos + len(value) + 20
        start = 0 if start < 0 else start
        end = length if end > length else end

        return True, {'response' : text[start:end]}

    return False, None