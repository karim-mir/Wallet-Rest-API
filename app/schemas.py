from enum import Enum
from pydantic import BaseModel, Field


class OperationType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class OperationRequest(BaseModel):
    operation_type: OperationType
    amount: float = Field(gt=0, description="Сумма должна быть больше 0")


class WalletResponse(BaseModel):
    wallet: str
    balance: float
    created_at: str

    class Config:
        from_attributes = True


class OperationResponse(BaseModel):
    message: str
    new_balance: float


class ErrorResponse(BaseModel):
    detail: str
