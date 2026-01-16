import hashlib

import logging
from sqlmodel import SQLModel, create_engine, Session

from config import DATABASE_URL, DATABASE_PATH

logger = logging.getLogger(__name__)

# 创建引擎（check_same_thread=False 允许多线程访问）
engine = create_engine(
    DATABASE_URL,
    echo=False,  # 生产环境设为 False
    connect_args={"check_same_thread": False}
)

db_hash=None
# 创建所有表
def init_db():
    global db_hash
    SQLModel.metadata.create_all(engine)
    db_hash=get_db_hash()
    logger.info(f"Database initialized, current database hash is: {db_hash}")

# 获取数据库会话的依赖
def get_session():
    with Session(engine) as session:
        yield session


def get_db_hash()->str:
    with open(DATABASE_PATH, "rb") as f:
        digest = hashlib.file_digest(f, "sha256")
        return digest.hexdigest()

def check_db():
    curr_db_hash=get_db_hash()
    if db_hash!=curr_db_hash:
        logger.info(f"Database modified. Database hash: {curr_db_hash}")
    else:
        logger.warning(f"Database not modified, please make sure that's correct. Database hash : {curr_db_hash}")