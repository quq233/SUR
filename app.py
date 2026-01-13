from collections import defaultdict

import uvicorn
from sqlmodel import Session, select

from config import SOURCE_MAC
from models import Device,Gateway

from database import engine
from utils import send_ra
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()

def daemon():
    with Session(engine) as session:  # 直接用 with Session
        # 1. 查询所有设备
        devices = session.exec(select(Device)).all()

        # 2. 查询所有 Gateway 并按 tag_id 分组
        gateways = session.exec(select(Gateway).order_by(Gateway.id)).all()
        tag_gateways = defaultdict(list)
        for gw in gateways:
            tag_gateways[gw.tag_id].append(gw)

        # 3. 为每个设备分配 Gateway 并发送 RA
        for device in devices:
            gateways_list = tag_gateways.get(device.tag_id, [])
            if not gateways_list:
                continue

            # MAC 地址哈希负载均衡
            mac_int = int(device.mac.replace(':', '').replace('-', '').lower(), 16)
            gateway = gateways_list[mac_int % len(gateways_list)]

            send_ra(
                dst_mac=device.mac,
                dst_lla="ff02::1",
                src_mac=gateway.mac,
                src_lla=gateway.local_ipv6,
                real_mac=SOURCE_MAC
            )
    pass

if __name__ == "__main__":
    daemon()
    scheduler.add_job(daemon, 'interval', minutes=3)
    scheduler.start()

    try:
        # 关闭热重载，避免 scheduler 重复启动
        uvicorn.run(
            "api:app",
            host="0.0.0.0",
            port=8000,
            reload=False
        )
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()