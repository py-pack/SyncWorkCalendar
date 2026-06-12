# Tech Context

## Розкладка монорепо

Репозиторій розділено на дві частини (зміна `restructure-monorepo-frontend`,
`decisinLog.md` → D-012):

- **`api/`** — Python-бекенд; пакет імпортується як `app` (фізично
  `api/app/`). Тут лежать `pyproject.toml`, `uv.lock`, `.python-version`,
  `alembic.ini`, `migrations/`, `run_api.py`, `main.py`, ноутбуки,
  `.env.template` (бекендні дефолти). Усі бекенд-команди виконуються **з теки
  `api/`**.
- **`front/`** — веб-фронтенд на Vue 3 + Vite + TypeScript (див. секцію
  «Frontend»).
- **Спільне на корені:** `docs/`, `openspec/`, Docker
  (`docker-compose.yml` + per-folder `Dockerfile`), кореневий `Makefile`,
  спільний `.env` (його читають і бекенд, і docker-compose).

## Runtime (backend, `api/`)

- **Python** `>=3.12,<4.0`, фактично запінено на **3.14** через
  `api/.python-version` (узгоджено з `dom-ex.bot`). Менеджер залежностей — `uv`
  (`api/pyproject.toml`, `api/uv.lock`; `poetry.lock` видалено).
- **Entry points**:
  - `uv run main.py` — лінійний скрипт `sync_time_camp()` + `sync_jira()`
    (хардкод періоду `2024-07-01 .. 2024-07-31`).
  - `main.ipynb` — інтерактивна оркестрація через `TimeCampUpdateTask`,
    `UpdateJiraTask`, `WorllogSyncTask`. Використовує `nest_asyncio.apply()`,
    щоб гнати async усередині ноутбука.
  - `run_api.py` — HTTP API (див. секцію «API»).
  - `python -m app.cli <command>` — argparse-CLI з авто-реєстрацією команд
    (`app/cli/commands/`); поточна команда — `add_user`. Тех-довідка по
    модулю і як додати команду — [../technical/cli.md](../technical/cli.md).

## Бібліотеки

- `fastapi`, `uvicorn[standard]` — HTTP-шар (capability `add-rest-api`).
- `python-jose[cryptography]` — JWT HS256 (`app/api/auth.py`).
- `bcrypt` (прямий, `>=4.0`) — хешування паролів `api_users.password_hash`
  у `app/api/auth.py`. `passlib` прибрано — несумісний із `bcrypt` 5.x на
  Python 3.14 (`decisinLog.md` → D-011).
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
- Локальний порт — `11331 → 5432`.
- Дані лежать у `.db/data`, дампи у `.db/dump`.
- Змінні: `APP__DB__HOST/PORT/DATABASE/USER/PASSWORD` + `ECHO`, `ECHO_POOL`,
  `POOL_SIZE`, `MAX_OVERFLOW`.
- Тех-доки по БД — тека [../technical/database/](../technical/database/):
  `schema.md` (поля, типи, індекси, soft-links, quirks) і `erd.md`
  (Mermaid ER, data flow, state-machine). Як інтроспектувати БД наживо —
  скіл `db-introspection`.

## Конфігурація

`app/config.py` (`pydantic-settings`) вантажить env-файли за **абсолютними**
шляхами (бо cwd бекенду — `api/`). Джерела за зростанням пріоритету
(пізніші перекривають раніші; реальні OS/compose env-змінні — над усіма):

1. `api/.env.template` — бекендні дефолти (комітиться).
2. `<root>/.env` — спільний конфіг (його ж читає `docker-compose.yml`).
3. `api/.env` — локальний override розробника (опційний, у `.gitignore`,
   у Docker-образ не бакається).

Префікс `APP__`, вкладеність через `__`, `env_ignore_empty=True` (порожні
значення з шаблону не затирають реальні). Активні секції:

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

## Команди (backend)

Виконуються **з теки `api/`** (там `pyproject.toml`/`uv.lock`/`.venv`):

```sh
cd api

# Встановити залежності (створює api/.venv із uv.lock)
uv sync

# Підняти БД (docker-compose на корені)
docker compose -f ../docker-compose.yml up -d db

# Міграція до останнього / нова ревізія
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "<slug>"

# Запуск (CLI-сценарій)
uv run main.py

# Запуск HTTP API
uv run run_api.py            # або: uv run uvicorn app.api.app:app --reload

# argparse-CLI (керування застосунком)
uv run python -m app.cli add_user        # завести користувача api_users
```

Кореневий `Makefile` має шорткати, які самі роблять `cd api && uv run …`:
`make serve` (HTTP API), `make dev` (uvicorn --reload), `make add-user`,
`make cli ARGS="..."`, `make sync`. Frontend: `make front-dev`,
`make front-build`.

## Frontend (`front/`)

- **Vue 3** + **Vite** + **TypeScript**; маршрутизація — `vue-router`,
  стейт — **Pinia**, HTTP-клієнт — рідний **`fetch`** (без `axios`,
  `front/src/api/client.ts`). Менеджер — `npm`.
- Базовий URL API — з `import.meta.env.VITE_API_BASE_URL` (env, не хардкод).
  У dev фронт ходить в API через **Vite-проксі** (`/api` → бекенд; ціль —
  `VITE_API_PROXY_TARGET`, `http://localhost:10331` локально /
  `http://api:10331` у docker-compose), тож один origin і CORS не потрібен.
- Команди (з теки `front/`): `npm install`, `npm run dev` (dev-server
  `:10332`), `npm run build` (`vue-tsc --noEmit` + `vite build` → `dist/`).
- Env: `front/.env.development` (несекретні dev-дефолти),
  `front/.env.example` (шаблон).

## Dev-середовище (Docker + host-nginx + HMR)

Повний гайд — [../technical/dev-environment.md](../technical/dev-environment.md).
Стисло:

- Доступ через host-nginx на кастомних доменах `http://sync.loc` і
  `https://sync.dev` (`docker/nginx.loc.conf`): `/` → Vite `:10332` (+ HMR-ws),
  `/api/` → бекенд `:10331` (зрізає префікс). `:10331`/`:10332` слухають
  localhost однаково — байдуже, docker чи host.
- **Конвенція host-портів** (щоб проекти не конфліктували): `10xxx` —
  сервіси (api `10331`, front `10332`), `11xxx` — БД (postgres `11331`).
  Суфікс `101` = цей проект. Задається в `docker-compose.yml`
  (`*_HOST_PORT`), `Makefile` (`API_PORT`/`FRONT_PORT`), `config.py`
  (`APIConfig.port`), `vite.config.ts` (`server.port`), `docker/nginx.loc.conf`.
- Hot-reload обох сервісів: `api` — `uvicorn --reload` із монтуванням `./api`
  + `WATCHFILES_FORCE_POLLING`; `front` — Vite + `VITE_USE_POLLING`
  (`.venv`/`node_modules` — з образів, анонімні томи).
- HMR за двома доменами: канонічний endpoint **`wss://sync.dev`** (env
  `VITE_HMR_*`), бо https-сторінка приймає лише `wss`; обслуговує і `sync.loc`.
  Потрібен довірений cert `sync.dev` (mkcert).
- Запуск: `docker compose up` (full stack) або `docker compose up -d db` +
  `make dev` + `make front-dev` (front/back на хості — найлегший HMR).

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
(або `uvicorn app.api.app:app`). OpenAPI рендериться на `/docs` і
`/redoc`. Тех-довідка — [api-reference.md](../technical/api-reference.md):
як стартувати, як завести першого користувача (ручний INSERT з bcrypt),
auth flow, lifecycle `api_jobs`, мапа endpoint-ів.

## Стандарти коду

- Форматтер: `black -l 79` (через alembic post-hook). Лінтера/типчекера наразі
  немає у проектних залежностях.
- Стиль імпортів — групами: stdlib → third-party → `app.*`.
- Іменування таблиць — `camel_case → snake_case + "s"` (див. `systemPatterns.md`).
