#encoding: utf-8
import time
import logging

import netaddr
import nmap

logger = logging.getLogger(__name__)


def run(job_params, plugin_info, plugin_config, *args, **kwargs):
    hosts = job_params.get('ip', [])
    ports = job_params.get('port', '0-1024')
    hosts = [' '.join(netaddr.iprange_to_globs(*x)) for x in hosts]

    nm = nmap.PortScanner()
    logger.debug(nm.scan(hosts=' '.join(hosts), ports=ports, arguments='-sV -O'))
    for host in nm.all_hosts():
        host_info = nm[host]
        os_info = ''
        try:
            os_info = host_info['osmatch'][0]['name']
        except BaseException as e:
            pass

        apps = []
        for protocol in host_info.all_protocols():
            for port_num, port_info in host_info[protocol].items():
                port = port_info.copy()
                port['protocol'] = protocol
                port['port'] = port_num
                apps.append(port)


        yield host, {
            'ip' : host,
            'name' : host_info.hostname(),
            'apps' : apps,
            'os' : os_info,
            'mac' : host_info.get('addresses').get('mac', ''),
        }