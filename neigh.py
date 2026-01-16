import platform
from typing import List
import logging
if platform.system() == "Linux":
    from pyroute2 import IPRoute
from scapy.all import srp1
from scapy.layers.l2 import Ether, ARP
import socket

from config import IFACE
from models import IPv6Neighbor
logger = logging.getLogger(__name__)

def get_ipv6_neighs() -> List[IPv6Neighbor]:
    if platform.system() != "Linux":
        return []
    result = []
    try:
        with IPRoute() as ipr:
            # 获取网卡索引
            links = ipr.link_lookup(ifname=IFACE)
            if not links:
                return []
            idx = links[0]

            # 获取邻居表
            neighbours = ipr.get_neighbours(ifindex=idx, family=socket.AF_INET6)

            for neigh in neighbours:
                attrs_dict = dict(neigh['attrs'])
                ipv6_addr = attrs_dict.get('NDA_DST')
                mac_addr = attrs_dict.get('NDA_LLADDR')

                if ipv6_addr and mac_addr and ipv6_addr.startswith('fe80'):
                    result.append(IPv6Neighbor(
                        local_ipv6=ipv6_addr,
                        mac=mac_addr
                    ))
    except Exception as e:
        # 记录日志或处理 Linux 下权限不足等问题
        logger.error(f"Error accessing netlink: {e}")

    return result


def ipv4_to_mac(ip, iface):
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
    ans = srp1(pkt, iface=iface, timeout=1, verbose=False)
    if ans:
        return ans.hwsrc.lower()
    return None

if __name__=="__main__":
    print(get_ipv6_neighs())

