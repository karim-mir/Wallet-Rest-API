import models
import schemas
from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])


@router.post(
    "/{wallet_uuid}/operation",
    response_model=schemas.OperationResponse,
    responses={
        400: {"model": schemas.ErrorResponse},
        404: {"model": schemas.ErrorResponse},
    },
)
async def change_balance(
    wallet_uuid: str,
    operation: schemas.OperationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Изменить баланс кошелька с использованием блокировок FOR UPDATE
    для предотвращения race conditions.
    """
    try:
        # Начинаем транзакцию
        await db.begin()

        # Блокируем строку кошелька для обновления (FOR UPDATE)
        # Если кошелька нет, создадим его позже (только для DEPOSIT)
        if operation.operation_type == schemas.OperationType.DEPOSIT:
            result = await db.execute(
                select(models.Wallet)
                .where(models.Wallet.uuid == wallet_uuid)
                .with_for_update()
            )
            wallet = result.scalar_one_or_none()

            if wallet:
                wallet.balance += operation.amount
            else:
                # Создаём новый кошелёк
                wallet = models.Wallet(uuid=wallet_uuid, balance=operation.amount)
                db.add(wallet)

            await db.commit()
            await db.refresh(wallet)

            return {
                "message": "Депозит выполнен успешно",
                "new_balance": wallet.balance,
            }

        elif operation.operation_type == schemas.OperationType.WITHDRAW:
            # Для списания кошелёк должен существовать
            result = await db.execute(
                select(models.Wallet)
                .where(models.Wallet.uuid == wallet_uuid)
                .with_for_update(nowait=True)  # nowait - не ждать, если заблокирован
            )
            wallet = result.scalar_one_or_none()

            if not wallet:
                await db.rollback()
                raise HTTPException(status_code=404, detail="Кошелек не найден")

            if operation.amount > wallet.balance:
                await db.rollback()
                raise HTTPException(
                    status_code=400, detail="Недостаточно средств на счете"
                )

            wallet.balance -= operation.amount
            await db.commit()
            await db.refresh(wallet)

            return {
                "message": "Списание выполнено успешно",
                "new_balance": wallet.balance,
            }

    except Exception as e:
        await db.rollback()
        # Проверяем, если это ошибка блокировки
        if "could not obtain lock" in str(e).lower():
            raise HTTPException(
                status_code=409,  # Conflict
                detail="Операция уже выполняется. Попробуйте позже.",
            )
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get(
    "/{wallet_uuid}",
    response_model=schemas.WalletResponse,
    responses={404: {"model": schemas.ErrorResponse}},
)
async def get_balance(
    wallet_uuid: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Получить баланс кошелька.
    """
    result = await db.execute(
        select(models.Wallet).where(models.Wallet.uuid == wallet_uuid)
    )
    wallet = result.scalar_one_or_none()

    if not wallet:
        raise HTTPException(status_code=404, detail="Кошелек не найден")

    return {
        "wallet": wallet.uuid,
        "balance": wallet.balance,
        "created_at": wallet.created_at.isoformat() if wallet.created_at else None,
    }
