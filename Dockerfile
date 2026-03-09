FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python -m venv /venv

COPY requirements.txt .
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt

# ---

FROM python:3.12-slim

RUN useradd --create-home --shell /bin/sh app

WORKDIR /app

COPY --from=builder /venv /venv

COPY --chown=app:app . .

RUN mkdir -p /app/log && chown -R app:app /app/log

USER app

ENV PATH="/venv/bin:$PATH" \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8050

CMD ["python", "app.py"]
