# CLAUDE.md — `api/` (Python-бекенд)

> Кореневий `CLAUDE.md` + `docs/memory-bank/` читаються першими. Тут — лише
> локальні нюанси бекенду; повні правила — у [`AGENTS.md`](AGENTS.md).

## Швидкий старт

Усе виконується **з теки `api/`** (пакет `app`, менеджер `uv`):

```sh
uv sync                                  # оточення
uv run python run_api.py                 # HTTP API (треба APP__API__JWT_SECRET)
uv run uvicorn app.api.app:app --reload  # dev hot-reload
uv run python -m app.cli add_user        # CLI
uv run alembic upgrade head              # міграції
```

Або кореневі шорткати: `make serve`, `make dev`, `make cli ARGS="…"`,
`make add-user`, `make sync`.

## Ключові застереження

- Зміна `app/models/*` → обов'язкова alembic-ревізія (head `ef2c7288bbb0`).
- `BaseDAO.sync_all` — full replace; для часткових worklog/entry —
  `sync_all_between`/`update_by_keys`.
- Деталі архітектури, state-machine та рішень — у Memory Bank
  (`systemPatterns.md`, `decisinLog.md`).

## Скіли (легкі вказівники)

`memory-bank-manager` (Memory Bank), `technical-docs-writer` (тех-доки),
`undocumented-behavior-finder` (прихована логіка). PHP-скіли не застосовні.
