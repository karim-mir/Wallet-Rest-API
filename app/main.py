import os
from datetime import datetime
from enum import Enum

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Float, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

app = FastAPI()

# DB settings
DB_NAME = os.getenv("DB_NAME", "wallet_db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_USER = os.getenv("DB_USER", "")

# DB строка для подключения
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# DB движок
engine = create_engine(DATABASE_URL)

# Сессии
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# DB модель
class WalletDB(Base):
    __tablename__ = "wallets"

    uuid = Column(String, primary_key=True, index=True)
    balance = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# DB создание таблиц
Base.metadata.create_all(bind=engine)


# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class OperationType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class OperationRequest(BaseModel):
    operation_type: OperationType
    amount: float = Field(gt=0, description="Сумма должна быть больше 0")


@app.post(
    "/api/v1/wallets/{WALLET_UUID}/operation",
    tags=["Баланс кошелька"],
    summary="Изменить баланс кошелька",
)
async def post_wallets(
    WALLET_UUID: str, operation: OperationRequest, db: Session = Depends(get_db)
):

    wallet = db.query(WalletDB).filter(WalletDB.uuid == WALLET_UUID).first()

    if operation.operation_type == OperationType.DEPOSIT:
        if wallet:
            wallet.balance += operation.amount
        else:
            wallet = WalletDB(uuid=WALLET_UUID, balance=operation.amount)
            db.add(wallet)

        db.commit()
        db.refresh(wallet)

        return {"message": "Депозит выполнен успешно", "new_balance": wallet.balance}

    elif operation.operation_type == OperationType.WITHDRAW:
        if not wallet:
            return {"error": "Кошелек не найден"}

        if operation.amount > wallet.balance:
            return {"error": "Недостаточно средств на счете"}

        wallet.balance -= operation.amount
        db.commit()
        db.refresh(wallet)

        return {"message": "Списание выполнено успешно", "new_balance": wallet.balance}


@app.get(
    "/api/v1/wallets/{WALLET_UUID}",
    tags=["Баланс кошелька"],
    summary="Получить баланс кошелька",
)
async def get_wallets(WALLET_UUID: str, db: Session = Depends(get_db)):
    wallet = db.query(WalletDB).filter(WalletDB.uuid == WALLET_UUID).first()

    if not wallet:
        return {"error": "Кошелек не найден"}

    return {
        "wallet": wallet.uuid,
        "balance": wallet.balance,
        "created_at": wallet.created_at.isoformat() if wallet.created_at else None,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
