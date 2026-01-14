from dataclasses import dataclass
from typing import Optional, List

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON


# 标签模型
class Tag(SQLModel, table=True):
    __tablename__ = "tags"

    tag_id: Optional[int] = Field(default=None, primary_key=True)
    alias: str = Field(index=True)
    dns: List[str] = Field(default_factory=list, sa_column=Column(JSON))


# 设备模型
class Device(SQLModel, table=True):
    __tablename__ = "devices"

    mac: str = Field(primary_key=True, max_length=17)
    tag_id: int = Field(foreign_key="tags.tag_id")
    alias: Optional[str] = None


# 网关模型
class Gateway(SQLModel, table=True):
    __tablename__ = "gateways"

    mac: str = Field(primary_key=True, max_length=17)
    tag_id: int = Field(foreign_key="tags.tag_id")
    alias: Optional[str] = None
    local_ipv6: str

@dataclass
class IPv6Neighbor:
    local_ipv6: str
    mac: str
