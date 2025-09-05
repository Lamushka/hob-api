# Human-or-Bot Classifier API — Starter

Минимальный HTTP API на **FastAPI** для интеграции с **Human or Bot**.

## Что есть
- `POST /v1/predict` — синхронный эндпоинт, возвращающий `prob_bot`.
- `GET /healthz`, `GET /readyz`, `GET /version` — сервисные эндпоинты.
- Авторизация: Bearer (`Authorization: Bearer <API_KEY>`), опционально HMAC-подпись `X-HoB-Signature`.

## Быстрый старт (локально)
```bash
python -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn pydantic
export API_KEY=dev_key_123
# (опционально) export HMAC_SECRET=super_secret
uvicorn main:app --reload --port 8000
```

Проверка:
```bash
curl -s http://127.0.0.1:8000/healthz
```

## Тестовый запрос к predict
```bash
BODY='{"message_id":"11111111-1111-1111-1111-111111111111","text":"привет, как дела?","lang":"ru"}'
# Если используете HMAC:
# SIG=$(python -c 'import os,hmac,hashlib;import sys;body=os.environ.get("BODY","");print(hmac.new(os.getenv("HMAC_SECRET","").encode(), body.encode(), hashlib.sha256).hexdigest())')
curl -s -X POST http://127.0.0.1:8000/v1/predict  -H "Authorization: Bearer $API_KEY"  -H "Content-Type: application/json"  -H "X-Request-ID: local-test-1"  ${SIG:+-H "X-HoB-Signature: $SIG"}  -d "$BODY" | jq .
```

## OpenAPI
Файл спецификации: `openapi.yaml`. Импортируйте в Postman/Insomnia или отправьте команде HoB.

## Деплой

### Вариант 1 — Render
- Подключите репозиторий, установите переменные `API_KEY`, `HMAC_SECRET`.
- Старт-команда: `uvicorn main:app --host 0.0.0.0 --port $PORT`.

### Вариант 2 — Google Cloud Run
- Соберите Docker-образ, задеплойте, добавьте секреты, включите автоскейл.

### Вариант 3 — Docker/VM
```bash
cat > Dockerfile <<'DOCKER'
FROM python:3.11-slim
WORKDIR /app
COPY main.py .
RUN pip install fastapi uvicorn pydantic
ENV PORT=8000
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]
DOCKER

docker build -t hob-api .
docker run -e API_KEY=prod_key -p 80:8000 hob-api
```

## Советы для интеграции с HoB
- Разведите `staging` и `prod` (два URL).
- Включите идемпотентность по `message_id` (кэш ответа на 24–72ч).
- Возвращайте `model_version` — удобно для A/B-сравнений.
- Настройте алерты на 5xx и p95 latency.
