import platform
from typing import List

from scapy.all import srp1
from scapy.layers.l2 import Ether, ARP
from pyroute2 import IPRoute
import socket

from config import IFACE
from models import IPv6Neighbor

ipr = IPRoute()
def get_ipv6_neighs()->List[IPv6Neighbor]:
    if platform.system() != "Linux":
        return []
    result=[]
    idx = ipr.link_lookup(ifname=IFACE)[0]
    neighbours = ipr.get_neighbours(ifindex=idx, family=socket.AF_INET6)

    # 提取 fe80 开头的 IPv6 和对应 MAC
    for neigh in neighbours:
        attrs_dict = dict(neigh['attrs'])

        ipv6_addr = attrs_dict.get('NDA_DST')
        mac_addr = attrs_dict.get('NDA_LLADDR')

        # 只提取 fe80 开头的链路本地地址
        if ipv6_addr and mac_addr and ipv6_addr.startswith('fe80'):
            result.append(IPv6Neighbor(
                local_ipv6=ipv6_addr,
                mac=mac_addr
            ))
            #print(f"{ipv6_addr}-{mac_addr}")

    return result

def ipv4_to_mac(ip, iface):
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
    ans = srp1(pkt, iface=iface, timeout=1, verbose=False)
    if ans:
        return ans.hwsrc.lower()
    return None

