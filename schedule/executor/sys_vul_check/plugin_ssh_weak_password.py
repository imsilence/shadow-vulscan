#encoding: utf-8
import logging
import traceback
import paramiko

TYPE = 'script'
IDENT = 'ssh_weak_password'
NAME = 'SSH弱口令'
LEVEL = 10
REMARK = 'SSH弱口令'

DEFAULT_PORTS = [22]
DEFAULT_USERNAMES = []
DEFAULT_PASSWORDS = []

logger = logging.getLogger(__name__)

def run(job_params, plugin_info, plugin_config, *args, **kwargs):
    ident = plugin_info.ident
    ip = job_params.get('ip', '')

    ports = plugin_config.get('ports', DEFAULT_PORTS)
    usernames = plugin_config.get('usernames', DEFAULT_USERNAMES)
    passwords = plugin_config.get('passwords', DEFAULT_PASSWORDS)

    flag, payloads = check(ip, ports, usernames, passwords)

    if flag:
        yield ip, {
            ident : {
                'payloads' : payloads
            }
        }

    yield ip, None


def check(ip, ports, usernames, passwords):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        for port in ports:
            for username in usernames:
                for password in passwords:
                    ssh.connect(ip, port, username, password)
                    return True, {'username' : username, 'password' : password}
    except BaseException as e:
        logger.debug(e)
        logger.debug(traceback.format_exc())
    finally:
        ssh.close()

    return False, None