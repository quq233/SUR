import httpx
import zipfile
import json

import asyncio

from config import WEBUI_DIR,VERSION_FILE,GITHUB_REPO
from utils import logger


class WebUIManager:
    def __init__(self):
        self.webui_dir = WEBUI_DIR
        self.version_file = VERSION_FILE

    async def get_latest_release(self):
        """获取最新 release 信息"""
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    def get_local_version(self):
        """获取本地版本"""
        if self.version_file.exists():
            with open(self.version_file) as f:
                return json.load(f).get("version")
        return None

    async def download_webui(self, download_url: str, version: str):
        """下载并解压 WebUI"""
        logger.info(f"Downloading WebUI version {version}...")

        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            response = await client.get(download_url)
            response.raise_for_status()

            zip_path = self.webui_dir / "webui.zip"
            with open(zip_path, "wb") as f:
                f.write(response.content)

            logger.info("Extracting WebUI...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.webui_dir)

            zip_path.unlink()

            # 保存版本信息
            with open(self.version_file, "w") as f:
                json.dump({"version": version}, f)

            logger.info(f"WebUI {version} ready!")

    async def ensure_webui(self, force_update=False):
        """确保 WebUI 存在且是最新版本"""
        self.webui_dir.mkdir(parents=True, exist_ok=True)

        try:
            release = await self.get_latest_release()
            latest_version = release["tag_name"]
            local_version = self.get_local_version()

            if force_update or local_version != latest_version:
                # 查找 dist.zip 资源
                asset = next(
                    (a for a in release["assets"] if a["name"] == "dist.zip"),
                    None
                )

                if asset:
                    await self.download_webui(asset["browser_download_url"], latest_version)
                else:
                    logger.warn("Warning: dist.zip not found in release assets")
            else:
                logger.info(f"WebUI is up to date (version {local_version})")

        except Exception as e:
            print(f"Error managing WebUI: {e}")
            if not (self.webui_dir / "index.html").exists():
                logger.error("WebUI not available and download failed")

if __name__ == "__main__":
    webui_manager = WebUIManager()
    asyncio.run(webui_manager.ensure_webui())