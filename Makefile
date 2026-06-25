.PHONY: serve dev cli add-user sync worker beat front-dev front-build

# Host-порти за конвенцією (10xxx — сервіси, 11xxx — БД), щоб проекти не
# конфліктували між собою. Перевизначити: `make dev API_PORT=10201`.
API_PORT   ?= 10331
FRONT_PORT ?= 10332
# Брокер Celery при host-run воркера/beat (контейнерний redis слухає 11332 на хості)
HOST_REDIS_URL ?= redis://localhost:11332/0

# --- Backend (запускається всередині api/) ---

# Запустити web-сервер (FastAPI) на конвенційному host-порту
serve:
	cd api && uv run uvicorn app.api.app:app --host 0.0.0.0 --port $(API_PORT)

# Те саме, але з hot-reload для розробки
dev:
	cd api && uv run uvicorn app.api.app:app --host 0.0.0.0 --port $(API_PORT) --reload

# CLI: проброс будь-яких аргументів, напр. `make cli ARGS="add_user --username john"`
cli:
	cd api && uv run python -m app.cli $(ARGS)

# Швидкий шорткат для додавання користувача
add-user:
	cd api && uv run python -m app.cli add_user

# Синхронізувати залежності бекенду
sync:
	cd api && uv sync

# Celery-воркер (host-run; redis — контейнерний на 11332). prefork +
# max-tasks-per-child як підстраховка від loop-binding asyncpg.
worker:
	cd api && APP__REDIS__URL=$(HOST_REDIS_URL) uv run celery -A app.celery_app worker --loglevel=info --pool=prefork --max-tasks-per-child=100

# Celery beat-планувальник (host-run; один екземпляр)
beat:
	cd api && APP__REDIS__URL=$(HOST_REDIS_URL) uv run celery -A app.celery_app beat --loglevel=info

# --- Frontend (запускається всередині front/) ---

# Vite dev-server на конвенційному host-порту
front-dev:
	cd front && npm run dev -- --port $(FRONT_PORT)

# Продакшн-збірка фронту
front-build:
	cd front && npm run build
