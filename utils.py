from collections import defaultdict
from typing import List

from apscheduler.schedulers.background import BackgroundScheduler
from scapy.layers.inet6 import ICMPv6ND_RA, ICMPv6NDOptPrefixInfo, ICMPv6NDOptSrcLLAddr, IPv6, ICMPv6NDOptRDNSS
from scapy.layers.l2 import Ether
from scapy.sendrecv import sendp
from sqlmodel import Session, select

from config import PREFIX, IFACE, RA_lifetime, RA_interval
from data.database import engine
from models import Device, Gateway, Tag


def send_ra(dst_mac, dst_lla, src_mac, src_lla,dns: List[str], router_lifetime: int, real_mac=None):
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

def daemon():
    with Session(engine) as session:
        # 1. 查询所有设备
        devices = session.exec(select(Device)).all()

        # 2. 查询所有 Gateway 并按 tag_id 分组
        gateways = session.exec(select(Gateway)).all()
        tag_gateways = defaultdict(list)
        for gw in gateways:
            tag_gateways[gw.tag_id].append(gw)

        # 3. 查询所有 Tag 并按 tag_id 索引
        tags = session.exec(select(Tag)).all()
        tag_dict = {tag.tag_id: tag for tag in tags}

        # 4. 为每个设备分配 Gateway 并发送 RA
        for device in devices:
            gateways_list = tag_gateways.get(device.tag_id, [])
            if not gateways_list:
                continue

            # 获取该设备所在 tag 的 DNS
            tag = tag_dict.get(device.tag_id)
            dns_servers = tag.dns if tag else []

            # MAC 地址哈希负载均衡
            mac_int = int(device.mac.replace(':', '').replace('-', '').lower(), 16)
            gateway = gateways_list[mac_int % len(gateways_list)]

            send_ra(
                dst_mac=device.mac,
                dst_lla="ff02::1",
                src_mac=gateway.mac,
                src_lla=gateway.local_ipv6,
                dns=dns_servers,  # 传递 DNS 列表
                router_lifetime=RA_lifetime
            )

scheduler = BackgroundScheduler()
broadcast_job = scheduler.add_job(daemon, 'interval', seconds=RA_interval,misfire_grace_time=30,coalesce=True,max_instances=1)