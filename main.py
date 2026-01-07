from scapy.all import *
from scapy.layers.inet6 import ICMPv6ND_RA, ICMPv6NDOptPrefixInfo, ICMPv6NDOptSrcLLAddr, IPv6, ICMPv6NDOptRDNSS
import time

from scapy.layers.l2 import Ether

# --- 配置区 ---
IFACE = "br0"
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

def mac_to_lla(mac):
    """根据 EUI-64 标准将 MAC 转换为 Link-Local IPv6 地址"""
    parts = mac.split(':')
    # 翻转第1字节的第2位
    parts[0] = "{:02x}".format(int(parts[0], 16) ^ 2)
    # 中间插入 ff:fe
    lla = f"fe80::{parts[0]}{parts[1]}:{parts[2]}ff:fe{parts[3]}:{parts[4]}{parts[5]}"
    return lla

def refresh_ipv6_neigh():
    subprocess.run(['ping6', '-c', '2', '-I', 'eth0', 'ff02::1'])
    print("neigh 刷新完成")

def get_ipv6_by_mac(target_mac):
    target_mac = target_mac.lower()
    try:
        # 执行系统命令获取 IPv6 邻居表
        output = subprocess.check_output(["ip", "-6", "neigh", "show"]).decode('utf-8')

        # 正则匹配：fe80 开头的地址且对应指定的 MAC
        # 匹配格式示例: fe80::8c3:39ff:fe21:3863 dev eth0 lladdr 0a:0b:0c:0d:0e:0f STALE
        pattern = r"(fe80[0-9a-f:]+)\s+dev\s+\S+\s+lladdr\s+(" + target_mac + r")"

        matches = re.findall(pattern, output, re.IGNORECASE)

        # 过滤掉非活跃或不通的地址（可选）
        if matches:
            # 返回匹配到的第一个地址
            return matches[0][0]
    except Exception as e:
        print(f"Error: {e}")

    return None

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
while True:
    #刷新邻居列表
    refresh_ipv6_neigh()
    # 1. 给父母手机发 RA：网关指向【主路由】
    for p in DIRECT_DEVICE:
        send_ra(p, get_ipv6_by_mac(p),SIDE_MAC ,MAIN_MAC, MAIN_LLA)

    # 2. 给自己手机发 RA：网关指向【旁路由】
    for device_mac in PROXY_DEVICE:
        send_ra(device_mac, mac_to_lla(device_mac), SIDE_MAC,SIDE_MAC, SIDE_LLA)

    time.sleep(150)