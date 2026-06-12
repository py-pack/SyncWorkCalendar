# AGENTS.md — `api/` (Python-бекенд)

> Спершу прочитай кореневі `AGENTS.md` і `docs/memory-bank/`. Тут — лише
> нюанси бекенду.

## Стек і запуск

- Python `>=3.12,<4.0` (запінено на 3.14 через `api/.python-version`),
  менеджер залежностей — `uv`. Пакет — `app` (імпорти `from app.…`).
- Усі бекенд-команди виконуються **з теки `api/`** (там `pyproject.toml`,
  `uv.lock`, `.venv`, `alembic.ini`):
  - `uv sync` — оточення.
  - `uv run python run_api.py` — HTTP API (потрібен `APP__API__JWT_SECRET`).
  - `uv run uvicorn app.api.app:app --reload` — dev hot-reload.
  - `uv run python -m app.cli add_user` — CLI.
  - `uv run alembic upgrade head` / `revision --autogenerate -m "<slug>"`.
- Кореневий `Makefile` має шорткати (`make serve`, `make dev`, `make cli`,
  `make add-user`, `make sync`), які самі роблять `cd api && …`.

## Робочі правила

- Перед правкою моделей чи DAO — звір зі стейт-машиною `WorklogSyncTask`
  у `systemPatterns.md` та з рішеннями `D-005`, `D-006` у `decisinLog.md`.
- Будь-яка зміна `app/models/*` має супроводжуватись alembic-ревізією:
  `uv run alembic revision --autogenerate -m "<slug>"`. Не редагуй старі
  ревізії. Поточний head — `ef2c7288bbb0`.
- Не запускай `BaseDAO.sync_all` для часткових даних worklog/entry — це full
  replace. Користуйся `sync_all_between` або `update_by_keys`.
- При додаванні нового `JRProject` ключа не покладайся на `SyncTaskService`
  кеш — TTL 2 год (`D-003`).

## Скіли (легкі вказівники)

- PHP-скіли (`phpstorm-plugin:*`) до цього проекту **не застосовні** — це
  Python.
- Для Memory Bank — `memory-bank-manager`. Для документації —
  `technical-docs-writer`. Для прихованої логіки — `undocumented-behavior-finder`.
- Глибока БД-довідка/інтроспекція — `docs/technical/database/` + MCP
  `mcp__pycharm__*` (див. `.claude/settings.local.json`).
