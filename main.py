from scapy.all import *
from scapy.layers.inet6 import ICMPv6ND_RA, ICMPv6NDOptPrefixInfo, ICMPv6NDOptSrcLLAddr, IPv6, ICMPv6NDOptRDNSS
import time
import neigh
from scapy.layers.l2 import Ether

# --- 配置区 ---
from config import IFACE
PREFIX = "2001:db8::"  # 你的 NPTV6 前缀

# 主路由信息
MAIN_MAC = "70:37:8e:a9:96:00"
MAIN_LLA = "fe80::1"

# 旁路由信息
SIDE_MAC = "6e:80:5a:e0:46:fe"
SIDE_LLA = "fe80::6c80:5aff:fee0:46fe"

# 父母手机列表 (目标)
DIRECT_DEVICE = [
    "d2:8c:f5:e1:b4:f4",
]

# 我的手机 (目标)
PROXY_DEVICE = [
    "9c:9e:d5:48:01:cf",
]

DNS_SERVER=[
    "2001:db8::102",
    "2400:3200::1",
    "fe80::1"
]

def send_ra(dst_mac, dst_lla, real_mac, src_mac, src_lla, router_lifetime=300):
    if not dst_mac:
        print(f"[-] 向 {dst_mac}  发送 RA 失败，未能找到设备的ipv6")
    # 构造以太网头
    eth = Ether(src=real_mac, dst=dst_mac)
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
    # 构造源链路地址选项
    sll = ICMPv6NDOptSrcLLAddr(lladdr=src_mac)

    # 5. 构造 DNS 服务器 (RDNSS 选项)
    rdnss = ICMPv6NDOptRDNSS(dns=DNS_SERVER, lifetime=router_lifetime)

    # 合体发送
    pkt = eth / ip6 / ra / pref / sll / rdnss
    sendp(pkt, iface=IFACE, verbose=False)

    print(f"[+] 已向 {dst_mac} ({dst_lla}) 发送 RA，网关指向 {src_lla}")

if __name__ == "__main__":
    #sniffer = neigh.start_discovery_thread(IFACE)
    while True:
        #neigh.refresh_neighbors(IFACE)
        #time.sleep(2)  # 等待Ping响应

        # 1. 给父母手机发 RA：网关指向【主路由】
        for p in DIRECT_DEVICE:
            send_ra(p, "ff02::1",SIDE_MAC ,MAIN_MAC, MAIN_LLA)

        # 2. 给自己手机发 RA：网关指向【旁路由】
        for device_mac in PROXY_DEVICE:
            #send_ra(device_mac, neigh.get_ipv6_by_mac_fast(device_mac), SIDE_MAC,SIDE_MAC, SIDE_LLA)
            send_ra(device_mac, "ff02::1", SIDE_MAC, SIDE_MAC, SIDE_LLA)

        time.sleep(150)