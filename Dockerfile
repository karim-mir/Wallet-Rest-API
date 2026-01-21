FROM python:3.12-alpine

WORKDIR /app

# Устанавливаем системные зависимости
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev \
    openssl-dev

# Устанавливаем Poetry
RUN pip install poetry

# Копируем файлы Poetry
COPY pyproject.toml poetry.lock* ./

# Конфигурируем Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Копируем код приложения
COPY ./app /app/app
COPY alembic.ini /app/
COPY alembic /app/alembic

# Создаём не-root пользователя
RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Запускаем приложение
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]