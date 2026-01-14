from collections import defaultdict

import uvicorn
from sqlmodel import Session, select

from models import Device, Gateway, Tag

from database import engine
from utils import send_ra

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
            )
    pass

if __name__ == "__main__":
    # 关闭热重载，避免 scheduler 重复启动
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )