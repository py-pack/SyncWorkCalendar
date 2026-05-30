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

- `fastapi`, `uvicorn[standart]` — HTTP-шар (capability `add-rest-api`).
- `python-jose[cryptography]` — JWT HS256 (`src/api/auth.py`).
- `passlib[bcrypt]` — bcrypt-хешування паролів `api_users.password_hash`.
- `pydantic[email] ^2.8`, `pydantic-settings ^2.4`.
- `sqlalchemy[asyncio] ^2.0`, `asyncpg`, `psycopg2-binary` (для синхронного
  engine у `sync_sessin`).
- `greenlet` — обовʼязковий runtime-deps для `sqlalchemy.async` (без нього
  падає `await` усередині `AsyncSession`).
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
- `current_user` — `Jira key` поточного користувача (`APP__CURRENT_USER`);
  лишається як **fallback** для CLI/notebook-сценаріїв. HTTP-шар бере
  `worker_key` із JWT-claim (`api_users.worker_key`).
- `api.*` — конфіг HTTP-шару (`APP__API__HOST/PORT/JWT_SECRET/JWT_TTL_HOURS/CORS_ORIGINS`).
  `JWT_SECRET` обовʼязковий для старту API; CLI/notebook працює без нього.

## Міграції

- `alembic.ini` → `script_location = migrations`.
- `migrations/env.py` бере URL із `settings.db.url` (async), використовує
  `target_metadata = Base.metadata`.
- Файли версій іменуються `%Y_%m_%d_%H%M-<rev>_<slug>.py`.
- Post-hook — `black -l 79` для нових ревізій.
- Поточний head: `ef2c7288bbb0` (`add_api_layer_tables`, 2026-05-13) —
  додає `api_users` + `api_jobs` (+ enum `api_job_status_enum`).
  Попередній head — `b4117e0c3dd4` (`update column started_at jr_worklogs`,
  2024-10-02). Доменні моделі (`tc_*`, `jr_*`, `worklog_sync_tasks`,
  `key_templates`) відображені без додаткових міграцій.

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

# Запуск HTTP API
python run_api.py            # або: uvicorn src.api.app:app --reload
```

## Інтеграційні URL та автентифікація

- `TimeCamp`: GET `tasks`, GET `entries?from=...&to=...&format=json`. Заголовок
  `Authorization: Bearer <APP__TC__TOKEN>`.
- `Jira (on-prem)`: GET `api/2/project`, POST `api/2/search` (JQL).
- `Tempo`: POST `tempo-timesheets/4/worklogs`, POST `tempo-timesheets/4/worklogs/search`.
- Усі запити проходять через `_make_request` у відповідному `*Service`-класі.
- Глибока довідка по TimeCamp — [../technical/integrations/timecamp.md](../technical/integrations/timecamp.md).
- Глибока довідка по Jira + Tempo — [../technical/integrations/jira.md](../technical/integrations/jira.md).

## API

HTTP-шар підняли в межах зміни `add-rest-api`. Точка входу — `run_api.py`
(або `uvicorn src.api.app:app`). OpenAPI рендериться на `/docs` і
`/redoc`. Тех-довідка — [api-reference.md](../technical/api-reference.md):
як стартувати, як завести першого користувача (ручний INSERT з bcrypt),
auth flow, lifecycle `api_jobs`, мапа endpoint-ів.

## Стандарти коду

- Форматтер: `black -l 79` (через alembic post-hook). Лінтера/типчекера наразі
  немає у проектних залежностях.
- Стиль імпортів — групами: stdlib → third-party → `src.*`.
- Іменування таблиць — `camel_case → snake_case + "s"` (див. `systemPatterns.md`).
