# Wallet REST API
Микросервис для управления кошельками пользователей с `RESTful API`, разработанный на `FastAPI` с поддержкой асинхронных операций.

## Основные возможности
- Управление балансом: Депозит и списание средств

- Конкурентная безопасность: Гарантированная корректность при параллельных операциях

- Асинхронная архитектура: Высокая производительность с `FastAPI` и `asyncpg`

- Контейнеризация: Полная изоляция через `Docker` и `Docker Compose`

- Автоматические миграции: Управление схемой БД через `Alembic`

## API Endpoints
1. Изменение баланса кошелька
```
POST /api/v1/wallets/{wallet_uuid}/operation
```
Пример запроса:

```
{
  "operation_type": "DEPOSIT",
  "amount": 1000
}
```
Типы операций:

- `DEPOSIT` - пополнение баланса

- `WITHDRAW` - списание средств

2. Получение баланса кошелька
```
GET /api/v1/wallets/{wallet_uuid}
```
Пример ответа:
```
{
  "wallet": "test-wallet-123",
  "balance": 1000,
  "created_at": "2024-01-20T10:30:00"
}
```
## Технологический стек
- `FastAPI` - асинхронный веб-фреймворк

- `SQLAlchemy 2.0` - асинхронный ORM

- `PostgreSQL` - основная база данных

- `Alembic` - система миграций

- `Docker` & `Docker Compose` - контейнеризация

- `Poetry` - управление зависимостями

- `Pydantic` - валидация данных

## Архитектура

```
WalletRestAPI/
├── app/
│   ├── database.py      # Конфигурация асинхронной БД
│   ├── models.py        # SQLAlchemy модели
│   ├── schemas.py       # Pydantic схемы
│   ├── wallets.py       # Эндпоинты кошельков
│   └── main.py          # Точка входа FastAPI
├── alembic/             # Миграции базы данных
├── tests/               # Тесты
└── pyproject.toml       # Зависимости Poetry
```
## Быстрый старт
### Требования
- `Docker 20.10+`

- `Docker Compose 2.0+`

1. Запуск приложения
Клонируйте репозиторий:

```
git clone <https://github.com/karim-mir/Wallet-Rest-API>
```

2. Запустите приложение одной командой:
```
docker-compose up --build
```
3. Приложение будет доступно по адресу:

```
API: http://localhost:8000

Swagger документация: http://localhost:8000/docs

ReDoc документация: http://localhost:8000/redoc

Health check: http://localhost:8000/health
```

## Тестирование

### Запустить все тесты
```
docker-compose exec app pytest -v
```

### Запустить конкретный тест
```
docker-compose exec app pytest tests/test_wallets.py -v
```

### Основные тестовые сценарии
- Создание кошелька через депозит

- Повторные депозиты

- Успешное списание

- Ошибка при недостатке средств

- Конкурентные операции

- Получение баланса

## Конкурентность
Для предотвращения `race conditions` реализованы:

- Блокировки уровня БД (`SELECT ... FOR UPDATE`)

- Асинхронные транзакции

- Оптимистичные блокировки для частых операций

## Конфигурация

1. Создайте `.env` файл на основе `.env.example`:
```
DB_NAME=wallet_db
DB_PORT=5432
DB_HOST=postgres
DB_PASSWORD=postgres
DB_USER=postgres
```
2. Docker Compose сервисы
- app: FastAPI приложение (порт 8000)

- postgres: PostgreSQL 15 (порт 5432)

3. Миграции базы данных
```
# Создание новой миграции
docker-compose exec app alembic revision --autogenerate -m "Описание изменений"

# Применение миграций
docker-compose exec app alembic upgrade head

# Откат миграции
docker-compose exec app alembic downgrade -1
```
## Отладка
### Просмотр логов

```
# Логи приложения
docker-compose logs app
```
```
# Логи базы данных
docker-compose logs postgres
```
```
# Логи в реальном времени
docker-compose logs -f app
```
### Доступ к базе данных
```
docker-compose exec postgres psql -U postgres -d wallet_db
```
```
# Пересборка и запуск
docker-compose up --build --force-recreate
```
```
# Остановка всех сервисов
docker-compose down
```

```
# Остановка с удалением томов
docker-compose down -v
```