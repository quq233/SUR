from scapy.all import srp1
from scapy.layers.l2 import Ether, ARP


def ipv4_to_mac(ip, iface):
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
    ans = srp1(pkt, iface=iface, timeout=1, verbose=False)
    if ans:
        return ans.hwsrc.lower()
    return None

