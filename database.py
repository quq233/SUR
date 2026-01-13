from sqlmodel import SQLModel, create_engine, Session
from contextlib import contextmanager

# SQLite 数据库文件
DATABASE_URL = "sqlite:///./app.db"

# 创建引擎（check_same_thread=False 允许多线程访问）
engine = create_engine(
    DATABASE_URL,
    echo=False,  # 生产环境设为 False
    connect_args={"check_same_thread": False}
)

# 创建所有表
def init_db():
    SQLModel.metadata.create_all(engine)

# 获取数据库会话的依赖
def get_session():
    with Session(engine) as session:
        yield session
