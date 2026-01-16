from pathlib import Path

IFACE='en0'
PREFIX = "2001:db8::"  # 你的 NPTV6 前缀
RA_lifetime=300
RA_interval=120

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = BASE_DIR / "app.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
print(BASE_DIR)
ENV_FILE = BASE_DIR / ".env"
WEBUI_DIR = BASE_DIR / "webui"
WEBUI_ROOT_DIR = WEBUI_DIR / "dist"
VERSION_FILE = WEBUI_DIR / "version.json"
GITHUB_REPO = "quq233/SUR-Dashboard"