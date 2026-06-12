.PHONY: serve dev cli add-user sync

# Запустити web-сервер (FastAPI) на host/port з .env
serve:
	uv run python run_api.py

# Те саме, але з hot-reload для розробки
dev:
	uv run uvicorn src.api.app:app --reload

# CLI: проброс будь-яких аргументів, напр. `make cli ARGS="add_user --username john"`
cli:
	uv run python -m src.cli $(ARGS)

# Швидкий шорткат для додавання користувача
add-user:
	uv run python -m src.cli add_user

# Синхронізувати залежності
sync:
	uv sync
