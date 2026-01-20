from enum import Enum
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict
import uvicorn

app = FastAPI()

class OperationType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"

class OperationRequest(BaseModel):
    operation_type: OperationType
    amount: float = Field(gt=0, description="Сумма должна быть больше 0")

wallets: Dict[str, float] = {}

@app.post("/api/v1/wallets/{WALLET_UUID}/operation", tags=["Баланс кошелька"], summary="Изменить баланс кошелька")
async def post_wallets(WALLET_UUID: str, operation: OperationRequest):

    if operation.operation_type == OperationType.DEPOSIT:
        current_balance = wallets.get(WALLET_UUID, 0)
        new_balance = current_balance + operation.amount
        wallets[WALLET_UUID] = new_balance
        return {"message": "Операция прошла успешно", "new_balance": new_balance}

    elif operation.operation_type == OperationType.WITHDRAW:
        if WALLET_UUID not in wallets:
            return {"error": "Кошелек не найден"}

        current_balance = wallets.get(WALLET_UUID)

        if operation.amount > current_balance:
            return {"error": "Недостаточно средств на счете"}


        new_balance = current_balance - operation.amount
        wallets[WALLET_UUID] = new_balance
        return {"message": "Списание выполнено успешно", "new_balance": new_balance}


@app.get("/api/v1/wallets/{WALLET_UUID}", tags=["Баланс кошелька"], summary="Получить баланс кошелька")
async def get_wallets(WALLET_UUID: str):

    if WALLET_UUID not in wallets:
        return {"error": "Кошелек не найден"}

    current_balance = wallets[WALLET_UUID]
    return {
        "wallet": WALLET_UUID,
        "balance": current_balance
    }


if __name__ == '__main__':
    uvicorn.run("main:app", host='0.0.0.0', port=5000, reload=True)