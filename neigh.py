import asyncio

from scapy.all import *
from scapy.layers.inet6 import IPv6, ICMPv6ND_NS, ICMPv6ND_NA, ICMPv6NDOptSrcLLAddr, ICMPv6EchoRequest
from scapy.layers.l2 import Ether

# 建立一个全局缓存，格式为 { "mac": "lla" }

def start_discovery_thread(iface,results: Dict[str, str]):
    def neighbor_callback(pkt):
        """
        回调函数：每当网卡抓到报文时，提取 IPv6 地址和 MAC 的对应关系
        """
        src_lla = pkt[IPv6].src
        src_mac = pkt[Ether].src.lower()
        results[src_mac] = src_lla
        print(f"pkt received from {src_lla} {src_mac}")

    """
    启动异步抓包，实时更新邻居表
    """
    t = AsyncSniffer(iface=iface, prn=neighbor_callback, store=0, filter="icmp6")
    t.start()
    return t


def refresh_neighbors(iface):
    print(f"[*] 正在向 {iface} 发送组播 Ping 探测所有节点...")
    ping_pkt = Ether(dst="33:33:00:00:00:01") / \
               IPv6(dst="ff02::1") / \
               ICMPv6EchoRequest()
    sendp(ping_pkt, iface=iface, verbose=False)
    print("[+] 探测包已发送，请检查邻居表更新。")

#def get_ipv6_by_mac_fast(target_mac):
#    return neighbor_cache.get(target_mac.lower())


async def scan_neighbors(iface):
    result = {}
    t=start_discovery_thread(iface=iface,results=result)
    refresh_neighbors(iface)
    await asyncio.sleep(2)
    t.stop()
    return result

if __name__ == "__main__":
    asyncio.run(scan_neighbors(iface="en0"))
