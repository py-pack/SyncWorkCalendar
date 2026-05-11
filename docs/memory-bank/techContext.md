# Tech Context

## Runtime

- **Python** `^3.12`, менеджер залежностей — `poetry` (`pyproject.toml`,
  `poetry.lock`).
- **Entry points**:
  - `python main.py` — лінійний скрипт `sync_time_camp()` + `sync_jira()`
    (хардкод періоду `2024-07-01 .. 2024-07-31`).
  - `main.ipynb` — інтерактивна оркестрація через `TimeCampUpdateTask`,
    `UpdateJiraTask`, `WorllogSyncTask`. Використовує `nest_asyncio.apply()`,
    щоб гнати async усередині ноутбука.

## Бібліотеки

- `fastapi`, `uvicorn[standart]` — заявлені, але не використовуються.
- `pydantic[email] ^2.8`, `pydantic-settings ^2.4`.
- `sqlalchemy[asyncio] ^2.0`, `asyncpg`, `psycopg2-binary` (для синхронного
  engine у `sync_sessin`).
- `alembic ^1.13`.
- `requests ^2.32` — для зовнішніх API (TimeCamp, Jira).
- `nest-asyncio ^1.6` — для ноутбука.
- dev: `black ^24.8`.

## БД

- **PostgreSQL** через `docker-compose.yml`, образ `leadsdoit/postgres:17.7`
  (див. шкіл `preferred-docker-images`).
- Локальний порт — `11101 → 5432`.
- Дані лежать у `.db/data`, дампи у `.db/dump`.
- Змінні: `APP__DB__HOST/PORT/DATABASE/USER/PASSWORD` + `ECHO`, `ECHO_POOL`,
  `POOL_SIZE`, `MAX_OVERFLOW`.
- Тех-доки по БД — тека [../technical/database/](../technical/database/):
  `schema.md` (поля, типи, індекси, soft-links, quirks) і `erd.md`
  (Mermaid ER, data flow, state-machine). Як інтроспектувати БД наживо —
  скіл `db-introspection`.

## Конфігурація

`pydantic-settings` парсить `.env.template` і `.env` (порядок мерджа саме такий).
Префікс `APP__`, вкладеність через `__`. Активні секції:

- `db.*` — підключення до Postgres.
- `tc.token` — `TimeCamp` API token (`APP__TC__TOKEN`).
- `jira.token` — `Jira` Bearer token (`APP__JIRA__TOKEN`).
- `current_user` — `Jira key` поточного користувача (`APP__CURRENT_USER`).

## Міграції

- `alembic.ini` → `script_location = migrations`.
- `migrations/env.py` бере URL із `settings.db.url` (async), використовує
  `target_metadata = Base.metadata`.
- Файли версій іменуються `%Y_%m_%d_%H%M-<rev>_<slug>.py`.
- Post-hook — `black -l 79` для нових ревізій.
- Поточний head: `b4117e0c3dd4` (`update column started_at jr_worklogs`,
  2024-10-02). Усі моделі вже відображені — `worklog_sync_tasks`, `key_templates`,
  `jr_*`, `tc_*`.

## Команди

```sh
# Підняти БД
docker compose up -d db

# Міграція до останнього
alembic upgrade head

# Згенерувати нову ревізію
alembic revision --autogenerate -m "<slug>"

# Запуск (CLI-сценарій)
python main.py
```

## Інтеграційні URL та автентифікація

- `TimeCamp`: GET `tasks`, GET `entries?from=...&to=...&format=json`. Заголовок
  `Authorization: Bearer <APP__TC__TOKEN>`.
- `Jira (on-prem)`: GET `api/2/project`, POST `api/2/search` (JQL).
- `Tempo`: POST `tempo-timesheets/4/worklogs`, POST `tempo-timesheets/4/worklogs/search`.
- Усі запити проходять через `_make_request` у відповідному `*Service`-класі.
- Глибока довідка по TimeCamp — [../technical/integrations/timecamp.md](../technical/integrations/timecamp.md).

## Стандарти коду

- Форматтер: `black -l 79` (через alembic post-hook). Лінтера/типчекера наразі
  немає у проектних залежностях.
- Стиль імпортів — групами: stdlib → third-party → `src.*`.
- Іменування таблиць — `camel_case → snake_case + "s"` (див. `systemPatterns.md`).
