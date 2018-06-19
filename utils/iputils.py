#encoding: utf-8

import netaddr
import math

class IPUtils(object):

    @staticmethod
    def ip_ranges(ip):
        nodes = []
        for node in ip.replace(',', ' ').replace(';', ' ').split():
            if node.find('-') != -1:
                nodes.append(tuple(map(netaddr.IPAddress, node.split('-'))))
            elif node.find('/') != -1:
                net = netaddr.IPNetwork(node)
                nodes.append([netaddr.IPAddress(net.first), netaddr.IPAddress(net.last)])
            else:
                nodes.append([netaddr.IPAddress(node), netaddr.IPAddress(node)])
        return nodes

    @staticmethod
    def split_ip_ranges(ip, count=3):
        rt = [[] for _ in range(count)]

        for node in IPUtils.ip_ranges(ip):
            start, end = int(node[0]), int(node[1])
            step = math.ceil((end - start + 1) / count)
            idx = 0
            while True:
                tmp = start + step
                if tmp < end:
                    rt[idx].append([netaddr.IPAddress(start), netaddr.IPAddress(tmp)])
                    start += step + 1
                else:
                    rt[idx].append([netaddr.IPAddress(start), netaddr.IPAddress(end)])
                    break

                idx += 1
        return list(filter(lambda x: x, rt))


if __name__ == '__main__':
    from pprint import pprint
    from functools import reduce
    ips = ['192.168.1.0/24']

    for ip in ips:
        print(ip + ':')
        pprint(IPUtils.split_ip_ranges(ip, 20))
