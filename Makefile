.PHONY: serve dev cli add-user sync front-dev front-build

# Host-порти за конвенцією (10xxx — сервіси, 11xxx — БД), щоб проекти не
# конфліктували між собою. Перевизначити: `make dev API_PORT=10201`.
API_PORT   ?= 10331
FRONT_PORT ?= 10332

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

# --- Frontend (запускається всередині front/) ---

# Vite dev-server на конвенційному host-порту
front-dev:
	cd front && npm run dev -- --port $(FRONT_PORT)

# Продакшн-збірка фронту
front-build:
	cd front && npm run build
