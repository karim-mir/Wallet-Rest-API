from fastapi import FastAPI
from routers import wallets
from database import engine, Base

app = FastAPI(
    title="Wallet REST API",
    description="API для работы с кошельками пользователей",
    version="1.0.0",
)

# Подключаем роутеры
app.include_router(wallets.router)


@app.on_event("startup")
async def startup():
    # Создаём таблицы (в продакшене используем миграции)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
