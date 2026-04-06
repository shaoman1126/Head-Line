from fastapi import FastAPI

from routers import news

app = FastAPI()

@app.get("/")
async def root():
    return {"msg": "Hello World"}



# 挂载路由 获取路由
app.include_router(news.router)