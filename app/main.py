from fastapi import FastAPI

from app.database import Base, engine
from app.wallets import router as wallets_router

app = FastAPI(
    title="Wallet REST API",
    description="API для работы с кошельками пользователей",
    version="1.0.0",
)

# Подключаем роутер кошельков
app.include_router(wallets_router)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/")
async def root():
    return {"message": "Wallet REST API", "docs": "/docs", "redoc": "/redoc"}
