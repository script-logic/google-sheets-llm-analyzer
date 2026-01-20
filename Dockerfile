FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY google_sheets_llm_analyzer_package/ ./google_sheets_llm_analyzer_package/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

COPY --chown=appuser:appuser . .

ENV PYTHONUNBUFFERED=1 
ENV PYTHONDONTWRITEBYTECODE=1

# Default
CMD ["python", "main.py", "--api"]