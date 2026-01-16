# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочий каталог
WORKDIR /app

# Копируем только файл зависимостей для кэширования
COPY pyproject.toml .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Создаем непривилегированного пользователя для безопасности
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Копируем исходный код (после установки зависимостей для кэширования)
COPY --chown=appuser:appuser . .

# Настройки среды
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Команда по умолчанию
CMD ["python", "main.py", "--api"]