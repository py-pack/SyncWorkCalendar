## Why

Зараз вся синхронізація `TimeCamp → Jira/Tempo` запускається з `main.py` або
ноутбука `main.ipynb`: довжина періоду й послідовність кроків зашиті у коді,
немає швидкого способу подивитись, які `tc_projects` помічені `is_sync=true`,
у якому статусі `worklog_sync_tasks`, чи є entries без зіставлення `meta.task`.
Налаштування `tc_projects.is_sync` і `tc_projects.issue_key` робиться руками
через PyCharm DataGrip. Це блокує введення в експлуатацію іншими користувачами
та не дозволяє побудувати UI зверху.

Потрібен REST API, який обгорне поточні таски, віддасть стан синхронізації та
дозволить керувати локальними прапорами `tc_projects` через мережу.

## What Changes

- Підняти **FastAPI** ASGI-додаток (`uvicorn`) на основі вже наявної залежності;
  створити роутер-структуру в `src/api/`.
- Додати **multi-user-ready authentication**: користувачі живуть у новій
  таблиці `api_users` (bcrypt password_hash, per-user `worker_key`); логін
  → Bearer JWT; усі запити (крім `/auth/login`, `/auth/refresh`, `/healthz`,
  `/docs`, `/openapi.json`) — за токеном. **API не створює юзерів
  автоматично** — заведення першого і наступних користувачів робиться
  ручним INSERT (тимчасово), повноцінне управління — окрема наступна
  зміна `add-user-management-cli`.
- Додати **read endpoints** для стану синхронізації:
    - `GET /tc-projects` — список TC-проектів із `is_sync`, `issue_key`,
      лічильниками entries за період.
    - `GET /jr-projects` — список Jira-проектів із `is_watched`, кількістю
      issues.
    - `GET /worklog-sync-tasks` — задачі синхронізації за період, з агрегованою
      статистикою по `StatusTaskEnum`.
    - `GET /tc-entries/untracked` — entries без `meta.task` і без
      `tc_project.issue_key` за період.
- Додати **sync trigger endpoints** — REST-обгортки навколо існуючих тасків
  `TimeCampUpdateTask`, `UpdateJiraTask`, `WorllogSyncTask`. Виконання
  синхронне (await), окремий нюанс довгих імпортів обговорено в `design.md`.
- Додати **TimeCamp project management**: `PATCH /tc-projects/{id}` для
  редагування `is_sync` і `issue_key`. Без `POST`/`DELETE` — id приходять із
  зовнішнього API.
- Додати **persistent job-tracking**: нова таблиця `api_jobs` (UUID PK,
  enum-статус, payload/result/error, timestamps, created_by/verified_by).
  Кожен sync-trigger створює рядок із статусом `running` → після успіху
  переходить у `needs_verification` → після ручного verify через
  `POST /api-jobs/{id}/verify` → `verified`. Failed-стан фінальний без
  verify.
- Додати endpoint-и керування jobs: `GET /api-jobs`, `GET /api-jobs/{id}`,
  `POST /api-jobs/{id}/verify`.
- Існуюча логіка тасків і DAO **не змінюється** (обгортка для api_jobs
  лежить на API-шарі). Дві нові alembic-ревізії: `api_users`, `api_jobs` +
  enum `api_job_status_enum`.
- Розширити `.env.template` змінними `APP__API__*` (host, port, JWT secret,
  JWT TTL, CORS origins).

Без breaking-змін у бізнес-моделях — додавання нового шару поверх існуючого.

## Capabilities

### New Capabilities

- `api-auth`: login за credentials із таблиці `api_users` → JWT, залежність
  `Depends(get_current_user)` для всіх захищених роутів. Початковий admin
  створюється з seed-конфігу.
- `api-jobs`: persistent журнал sync-операцій із проміжним статусом
  `needs_verification`. Endpoint-и list/get/verify. Wrapper для
  `sync-triggers`.
- `api-sync-status`: read-only endpoints, що показують стан локальних таблиць
  синхронізації за період і lookup-фільтрами.
- `api-sync-triggers`: write-only endpoints, що запускають існуючі sync-таски
  з body-параметрами періоду/ключів. Кожен виклик створює `api_jobs`-row.
- `api-tc-projects-management`: PATCH-endpoint для локальних прапорів
  `tc_projects.is_sync` і `tc_projects.issue_key`.

### Modified Capabilities

<!-- Раніше специфікацій не було (`openspec/specs/` порожній). Жодна існуюча
     capability не змінюється на рівні вимог. -->

## Impact

- **Новий код:** `src/api/` (роутери, DTO, dependencies), `src/api/auth.py`,
  `src/api/app.py` (точка входу FastAPI), нові моделі `src/models/api_user.py`
  і `src/models/api_job.py`, відповідні DAO в `src/dao/`, `run_api.py` (або
  `python -m src.api`) для `uvicorn`.
- **Нові таблиці БД:** `api_users`, `api_jobs` (+ enum
  `api_job_status_enum`). Дві alembic-ревізії.
- **Конфігурація:** додаткові секції `APP__API__*` у `.env.template` і
  `src/config.py`, включно з seed-admin і CORS.
- **Існуюча бізнес-логіка:** **не змінюється** — таски (`src/tasks/*`) і
  DAO (`src/dao/*`) переюзаються як є. `get_async_asession` стає FastAPI
  dependency.
- **Documentation:**
    - OpenAPI / Swagger UI віддає сам FastAPI на `/docs` і `/redoc`.
    - `docs/technical/api-reference.md` — нова технічна довідка (створиться
      в implement-фазі).
    - `docs/technical/database/schema.md` і `database/erd.md` — оновити з
      новими `api_users`, `api_jobs` (правило з SKILL `db-introspection` §8).
- **Memory Bank:** оновлення `activeContext.md`, `progress.md` після
  імплементації, новий пункт у `systemPatterns.md` про HTTP-шар і
  api_jobs-lifecycle.
- **Залежності:** `fastapi`, `uvicorn[standart]` уже заявлені у `pyproject.toml`.
  Додатково: `python-jose[cryptography]` (JWT) або `pyjwt`; `passlib[bcrypt]`
  для хешу пароля — вибір зафіксовано у `design.md`.
- **Ризики:** довгі sync-операції блокують HTTP-запит; накопичення
  непідтверджених `needs_verification`-jobs. Mitigation — у `design.md`.
