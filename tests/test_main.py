from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import Base, app, get_db

# Используем SQLite в памяти (не создаёт файлов)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Подменяем БД для тестов
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Создаём таблицы
Base.metadata.create_all(bind=engine)

# Тестовый клиент
client = TestClient(app)


def test_deposit_new_wallet():
    """Тест 1: Положить деньги на новый кошелёк"""
    response = client.post(
        "/api/v1/wallets/wallet-1/operation",
        json={"operation_type": "DEPOSIT", "amount": 1000},
    )

    # Проверяем, что ответ успешный
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Депозит выполнен успешно"
    assert data["new_balance"] == 1000
    print("Тест 1 пройден: Создание кошелька через депозит")


def test_deposit_existing_wallet():
    """Тест 2: Положить деньги на существующий кошелёк"""
    # Первый депозит
    client.post(
        "/api/v1/wallets/wallet-2/operation",
        json={"operation_type": "DEPOSIT", "amount": 500},
    )

    # Второй депозит
    response = client.post(
        "/api/v1/wallets/wallet-2/operation",
        json={"operation_type": "DEPOSIT", "amount": 300},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["new_balance"] == 800  # 500 + 300
    print("Тест 2 пройден: Второй депозит")


def test_withdraw_success():
    """Тест 3: Успешно снять деньги"""
    # Сначала кладём деньги
    client.post(
        "/api/v1/wallets/wallet-3/operation",
        json={"operation_type": "DEPOSIT", "amount": 1000},
    )

    # Потом снимаем
    response = client.post(
        "/api/v1/wallets/wallet-3/operation",
        json={"operation_type": "WITHDRAW", "amount": 400},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Списание выполнено успешно"
    assert data["new_balance"] == 600  # 1000 - 400
    print("Тест 3 пройден: Успешное списание")


def test_withdraw_wallet_not_found():
    """Тест 4: Ошибка при списании с несуществующего кошелька"""
    response = client.post(
        "/api/v1/wallets/unknown-wallet/operation",
        json={"operation_type": "WITHDRAW", "amount": 100},
    )

    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"] == "Кошелек не найден"
    print("Тест 4 пройден: Ошибка 'Кошелёк не найден'")


def test_withdraw_insufficient_funds():
    """Тест 5: Ошибка при недостатке средств"""
    # Кладём немного
    client.post(
        "/api/v1/wallets/wallet-4/operation",
        json={"operation_type": "DEPOSIT", "amount": 200},
    )

    # Пытаемся снять больше
    response = client.post(
        "/api/v1/wallets/wallet-4/operation",
        json={"operation_type": "WITHDRAW", "amount": 500},
    )

    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"] == "Недостаточно средств на счете"
    print("Тест 5 пройден: Ошибка 'Недостаточно средств'")


def test_get_existing_wallet():
    """Тест 6: Получить баланс существующего кошелька"""
    # Создаём кошелёк
    client.post(
        "/api/v1/wallets/wallet-5/operation",
        json={"operation_type": "DEPOSIT", "amount": 750},
    )

    # Получаем баланс
    response = client.get("/api/v1/wallets/wallet-5")

    assert response.status_code == 200
    data = response.json()
    assert data["wallet"] == "wallet-5"
    assert data["balance"] == 750
    print("Тест 6 пройден: Получение баланса")


def test_get_nonexistent_wallet():
    """Тест 7: Получить баланс несуществующего кошелька"""
    response = client.get("/api/v1/wallets/nonexistent")

    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"] == "Кошелек не найден"
    print("Тест 7 пройден: Баланс несуществующего кошелька")


def test_invalid_amount():
    """Тест 8: Ошибка при нулевой или отрицательной сумме"""
    response = client.post(
        "/api/v1/wallets/wallet-6/operation",
        json={"operation_type": "DEPOSIT", "amount": 0},  # Нельзя!
    )

    # FastAPI вернёт 422 при ошибке валидации
    assert response.status_code == 422
    print("Тест 8 пройден: Валидация суммы (нельзя 0)")


def test_full_scenario():
    """Тест 9: Полный сценарий (интеграционный тест)"""
    wallet_id = "test-full-wallet"

    # 1. Создаём кошелёк
    response = client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 2000},
    )
    assert response.json()["new_balance"] == 2000

    # 2. Проверяем баланс
    response = client.get(f"/api/v1/wallets/{wallet_id}")
    assert response.json()["balance"] == 2000

    # 3. Ещё депозит
    response = client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 500},
    )
    assert response.json()["new_balance"] == 2500

    # 4. Снимаем
    response = client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 800},
    )
    assert response.json()["new_balance"] == 1700

    # 5. Финальная проверка
    response = client.get(f"/api/v1/wallets/{wallet_id}")
    assert response.json()["balance"] == 1700

    print("Тест 9 пройден: Полный сценарий")


if __name__ == "__main__":
    print("Запуск упрощённых тестов для Wallet API")
    print("=" * 50)

    # Очистка базы перед тестами (простой способ)
    from sqlalchemy import text

    with engine.connect() as conn:
        conn.execute(text("DELETE FROM wallets"))
        conn.commit()

    # Запускаем все тесты по порядку
    tests = [
        test_deposit_new_wallet,
        test_deposit_existing_wallet,
        test_withdraw_success,
        test_withdraw_wallet_not_found,
        test_withdraw_insufficient_funds,
        test_get_existing_wallet,
        test_get_nonexistent_wallet,
        test_invalid_amount,
        test_full_scenario,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            # Очищаем таблицу перед каждым тестом
            with engine.connect() as conn:
                conn.execute(text("DELETE FROM wallets"))
                conn.commit()

            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"Ошибка в тесте {test_func.__name__}: {e}")

    print("=" * 50)
    print(f"Итог: {passed} пройдено, {failed} упало")

    if failed == 0:
        print("Все тесты пройдены успешно!")
    else:
        print(" Есть проблемы в тестах")
