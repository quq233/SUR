import uvicorn
from tinydb import TinyDB

db = TinyDB('db.json')


# 关键部分：直接在脚本中运行
if __name__ == "__main__":
    uvicorn.run(
        "api:app",   # 注意：这里建议传入字符串 "文件名:对象名"
        host="127.0.0.1",
        port=8000,
        reload=True   # 开发模式下开启热重载
    )