import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import uvicorn
from rich.logging import RichHandler
from scapy.all import conf as scapy_conf
from scapy.interfaces import get_if_list
from config import IFACE


def setup_logging():
    # 1.定义日志格式 (文件日志用)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # 2. 获取根 Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if not root_logger.handlers:
        # --- 控制台：使用 Rich 渲染 ---
        console_handler = RichHandler(
            level=logging.INFO,
            rich_tracebacks=True,
            markup=True  # 允许在日志中使用 [bold red]text[/] 这种标记
        )
        root_logger.addHandler(console_handler)

        file_handler = RotatingFileHandler(
            "app.log", maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)


def check_startup(interface):
    """
    执行启动检查：权限、网卡有效性以及 root 警告。
    """
    logger = logging.getLogger(__name__)
    # 1. 检查是否为 root 用户并发出警告
    # 在 Linux 系统中，root 的 UID 通常为 0
    if os.geteuid() == 0:
        logger.warning("当前以 root 用户运行，推荐使用 setcap")

    # 2. 检查网卡是否存在
    available_interfaces = get_if_list()
    if interface not in available_interfaces:
        logger.error(f"指定的网卡 '{interface}' 不存在。")
        logger.error(f"可用网卡列表: {', '.join(available_interfaces)}")
        sys.exit(1)

    try:
        test_socket = scapy_conf.L3socket()
        test_socket.close()
    except Exception as e:
        logger.error(f"Scapy初始化原始套接字时发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_logging()
    check_startup(interface=IFACE)
    from api import app
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False
    )