from pathlib import Path

IFACE='en0'
PREFIX = "2001:db8::"  # 你的 NPTV6 前缀
RA_lifetime=300
RA_interval=120

ENV_FILE = Path(".env")
WEBUI_DIR = Path("./webui")
WEBUI_ROOT_DIR = Path("./webui/dist")
VERSION_FILE = WEBUI_DIR / "version.json"
GITHUB_REPO = "quq233/SUR-Dashboard"