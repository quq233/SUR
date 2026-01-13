from typing import List, Optional, Generic, TypeVar, Type, Any, Dict
from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from tinydb import TinyDB, Query

from ipv4_neigh import ipv4_to_mac
# --- 1. 基础模型定义 ---
from models import Device, Gateway, Tag
from neigh import scan_neighbors
from config import IFACE

# --- 2. 泛型 CRUD 核心引擎 ---
T = TypeVar("T", bound=BaseModel)


class CRUDService(Generic[T]):
    def __init__(self, table_name: str, model: Type[T], id_field: str):
        self.db = TinyDB("db.json")
        self.table = self.db.table(table_name)
        self.model = model
        self.id_field = id_field
        self.query = Query()

    def create(self, obj: T) -> T:
        data = obj.model_dump()
        # 处理自增 ID (针对 Tag 等使用 int id 的情况)
        if self.id_field == "tag_id" and data.get("tag_id") is None:
            data["tag_id"] = len(self.table) + 1

        # 避免 ID/MAC 重复
        if self.table.contains(self.query[self.id_field] == data[self.id_field]):
            raise HTTPException(400, f"{self.id_field} already exists")

        self.table.insert(data)
        return self.model(**data)

    def get_all(self) -> List[T]:
        return [self.model(**item) for item in self.table.all()]

    def get_one(self, id_val: Any) -> T:
        item = self.table.get(self.query[self.id_field] == id_val)
        if not item:
            raise HTTPException(404, "Item not found")
        return self.model(**item)

    def update(self, id_val: Any, update_data: Dict) -> T:
        if not self.table.contains(self.query[self.id_field] == id_val):
            raise HTTPException(404, "Item not found")
        self.table.update(update_data, self.query[self.id_field] == id_val)
        return self.get_one(id_val)

    def delete(self, id_val: Any):
        if not self.table.contains(self.query[self.id_field] == id_val):
            raise HTTPException(404, "Item not found")
        self.table.remove(self.query[self.id_field] == id_val)
        return {"message": "deleted"}


# --- 3. 实例化业务逻辑 ---
# 这里一行代码就搞定了原本要写几十行的 CRUD
tag_service = CRUDService("tags", Tag, "tag_id")
device_service = CRUDService("devices", Device, "mac")
gateway_service = CRUDService("gateways", Gateway, "mac")

# --- 4. 路由组装 ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议改为前端具体域名
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/neighbors/")
async def list_neighbors():
    return await scan_neighbors(iface=IFACE)

@app.get("/ipv4/mac/")
async def get_ipv4_mac(ip: str):
    return ipv4_to_mac(iface=IFACE,ip=ip)
@app.get("")
#Tag 的路由
@app.post("/tags/", response_model=Tag)
def create_tag(tag: Tag): return tag_service.create(tag)

@app.get("/tags/", response_model=List[Tag])
def list_tags(): return tag_service.get_all()

@app.put("/tags/{tag_id}")
def update_tag(tag_id: int,tag: Tag):
    return tag_service.update(tag_id, tag.model_dump())

@app.delete("/tags/{tag_id}")
def delete_tag(tag_id: int):
    return tag_service.delete(tag_id)


#Device 的路由
@app.post("/devices/")
def create_device(device: Device): return device_service.create(device)

@app.get("/devices/")
def list_devices(): return device_service.get_all()

#@app.get("/devices/{mac}")
#def get_device(mac: str): return device_service.get_one(mac)
@app.put("/devices/{mac}")
def update_device(mac: str, device: Device):
    return device_service.update(mac, device.model_dump())

@app.delete("/devices/{mac}")
def delete_device(mac: str): return device_service.delete(mac)


#Gateway 的路由
@app.post("/gateways/")
def create_gateway(gw: Gateway):
    return gateway_service.create(gw)


@app.get("/gateways/")
def list_gateways(): return gateway_service.get_all()

@app.put("/gateways/{mac}")
def update_gateway(mac: str,gw: Gateway):
    return gateway_service.update(mac,gw.model_dump())

@app.delete("/gateways/{mac}")
def delete_gateway(mac: str):
    return gateway_service.delete(mac)
