import datetime
from contextlib import asynccontextmanager
from typing import List, Generic, TypeVar, Type

from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, select
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from config import IFACE, WEBUI_DIR, WEBUI_ROOT_DIR
from data.database import init_db, get_session
from models import Device, Gateway, Tag
from neigh import ipv4_to_mac, get_ipv6_neighs
from utils import daemon, broadcast_job, scheduler
from webui_manager import WebUIManager

# --- 泛型 CRUD 服务 ---
T = TypeVar("T")



class CRUDService(Generic[T]):
    def __init__(self, model: Type[T], id_field: str):
        self.model = model
        self.id_field = id_field

    def create(self, obj: T, session: Session) -> T:
        # 检查是否已存在
        id_val = getattr(obj, self.id_field)
        if id_val is not None:
            existing = session.get(self.model, id_val)
            if existing:
                raise HTTPException(400, f"{self.id_field} already exists")

        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

    def get_all(self, session: Session) -> List[T]:
        statement = select(self.model)
        return list(session.exec(statement).all())

    def get_one(self, id_val, session: Session) -> T:
        obj = session.get(self.model, id_val)
        if not obj:
            raise HTTPException(404, "Item not found")
        return obj

    def update(self, id_val, update_data: dict, session: Session) -> T:
        obj = session.get(self.model, id_val)
        if not obj:
            raise HTTPException(404, "Item not found")

        for key, value in update_data.items():
            if value is not None:  # 只更新非 None 的字段
                setattr(obj, key, value)

        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

    def delete(self, id_val, session: Session):
        obj = session.get(self.model, id_val)
        if not obj:
            raise HTTPException(404, "Item not found")

        session.delete(obj)
        session.commit()
        return {"message": "deleted"}


# --- 实例化服务 ---
tag_service = CRUDService(Tag, "tag_id")
device_service = CRUDService(Device, "mac")
gateway_service = CRUDService(Gateway, "mac")

# --- FastAPI 应用 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    await WebUIManager().ensure_webui()
    init_db()
    daemon()
    scheduler.start()
    yield
    scheduler.shutdown()
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---daemon控制
# ---daemon控制
@app.get("/api/broadcast/stop")
def stop_broadcast():
    if broadcast_job:
        broadcast_job.pause()
        return {"status": "success", "message": "Broadcast job paused"}
    raise HTTPException(status_code=500, detail="Job not found")

@app.get("/api/broadcast/start")
def start_broadcast():
    if broadcast_job:
        broadcast_job.resume()
        return {"status": "success", "message": "Broadcast job resumed"}
    raise HTTPException(status_code=500, detail="Job not found")

@app.get("/api/broadcast/")
def check_broadcast_job():
    if broadcast_job and broadcast_job.next_run_time is not None:
        return {
            "running": True,
            "next_run_time": broadcast_job.next_run_time.isoformat()
        }
    return {"running": False, "next_run_time": None}

@app.get("/api/broadcast/trigger_now")
def trigger_now():
    if broadcast_job:
        broadcast_job.modify(next_run_time=datetime.datetime.now())
        return {"status": "success", "message": "Broadcast triggered"}
    raise HTTPException(status_code=500, detail="Job not found")
# --- 网络扫描路由 ---
@app.get("/api/neighbors/")
def list_neighbors():
    return get_ipv6_neighs()


@app.get("/api/ipv4/mac/")
async def get_ipv4_mac(ip: str):
    return ipv4_to_mac(iface=IFACE, ip=ip)


# --- Tag 路由 ---
@app.post("/api/tags/", response_model=Tag)
def create_tag(tag: Tag, session: Session = Depends(get_session)):
    return tag_service.create(tag, session)


@app.get("/api/tags/", response_model=List[Tag])
def list_tags(session: Session = Depends(get_session)):
    return tag_service.get_all(session)


@app.put("/api/tags/{tag_id}", response_model=Tag)
def update_tag(tag_id: int, tag: Tag, session: Session = Depends(get_session)):
    return tag_service.update(tag_id, tag.model_dump(exclude_unset=True), session)


@app.delete("/api/tags/{tag_id}")
def delete_tag(tag_id: int, session: Session = Depends(get_session)):
    return tag_service.delete(tag_id, session)


# --- Device 路由 ---
@app.post("/api/devices/", response_model=Device)
def create_device(device: Device, session: Session = Depends(get_session)):
    return device_service.create(device, session)


@app.get("/api/devices/", response_model=List[Device])
def list_devices(session: Session = Depends(get_session)):
    return device_service.get_all(session)


@app.put("/api/devices/{mac}", response_model=Device)
def update_device(mac: str, device: Device, session: Session = Depends(get_session)):
    return device_service.update(mac, device.model_dump(exclude_unset=True), session)


@app.delete("/api/devices/{mac}")
def delete_device(mac: str, session: Session = Depends(get_session)):
    return device_service.delete(mac, session)


# --- Gateway 路由 ---
@app.post("/api/gateways/", response_model=Gateway)
def create_gateway(gw: Gateway, session: Session = Depends(get_session)):
    return gateway_service.create(gw, session)


@app.get("/api/gateways/", response_model=List[Gateway])
def list_gateways(session: Session = Depends(get_session)):
    return gateway_service.get_all(session)


@app.put("/api/gateways/{mac}", response_model=Gateway)
def update_gateway(mac: str, gw: Gateway, session: Session = Depends(get_session)):
    return gateway_service.update(mac, gw.model_dump(exclude_unset=True), session)


@app.delete("/api/gateways/{mac}")
def delete_gateway(mac: str, session: Session = Depends(get_session)):
    return gateway_service.delete(mac, session)




if (WEBUI_ROOT_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(WEBUI_ROOT_DIR / "assets")), name="assets")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """处理所有其他路由，返回 index.html 或静态文件"""
    file_path = WEBUI_ROOT_DIR / full_path

    # 如果是文件且存在，直接返回
    if file_path.is_file():
        return FileResponse(file_path)

    # 否则返回 index.html（用于 SPA 路由）
    index_path = WEBUI_ROOT_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    return {"error": "WebUI not found"}