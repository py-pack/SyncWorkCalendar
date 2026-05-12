## Context

Існуючий проект — async-Python CLI/notebook-утиліта без HTTP-шару. Точки
входу: `python main.py` і `main.ipynb`. Залежності `fastapi` й
`uvicorn[standart]` уже заявлені у `pyproject.toml`, але ніде не
ініціалізовуються. Поточний `current_user` бере `Jira key` зі змінної
оточення `APP__CURRENT_USER`.

Локальна Postgres БД (`db_swc`) має 8 доменних таблиць — повна довідка
у `docs/technical/database/schema.md`. Async-engine + контекст-менеджер
`get_async_asession()` уже існують і використовуються в усіх DAO.

Передбачаємо **multi-user-ready** ядро: користувачі живуть у таблиці
`api_users`, кожен має власний `worker_key` (Jira key) і `password_hash`.
Фактично робить синхронізацію один користувач, але архітектура дозволяє
додати ще без рефакторингу. Per-user OAuth-токени на Jira/TimeCamp —
окрема майбутня зміна, не зараз.

Друга концептуальна сутність — **`api_jobs`**: кожен виклик sync-endpoint-а
створює рядок із статусом, payload-ом і результатом. Сихронізація вважається
завершеною не одразу після `200 OK`, а через окремий етап
**`needs_verification → verified`**, на якому користувач підтверджує, що
дані виглядають коректно.

## Goals / Non-Goals

**Goals:**

- Підняти `FastAPI` app з модульною структурою `src/api/` (роутери по
  capabilities).
- Захистити всі мутаційні та read-stat endpoint-и одним механізмом
  автентифікації, що працює без зовнішніх систем (Keycloak, OAuth-провайдерів).
- Reuse повний існуючий стек: `get_async_asession`, DAO, таски,
  Pydantic-моделі. Не переписувати бізнес-логіку.
- Дати UI/Postman повну картину стану синхронізації за період + ручний
  контроль над `tc_projects.is_sync` і `tc_projects.issue_key`.
- OpenAPI-документація автогенерується FastAPI (`/docs`, `/redoc`,
  `/openapi.json`).

**Non-Goals:**

- **RBAC / permissions.** Усі активні `api_users` мають однаковий доступ.
  Ролі — окрема майбутня зміна.
- Async черга (Celery, RQ). Sync trigger-и виконуються синхронно або через
  `BackgroundTasks` (рішення нижче).
- Створення/видалення `tc_projects` і `jr_projects` — id приходять із
  зовнішніх API.
- WebSocket-стрім прогресу синку. Можна додати окремою зміною пізніше.
- Окрема Frontend SPA. Цей change — тільки backend + OpenAPI.
- Per-user OAuth-токени для Jira/TimeCamp. Усі `api_users` поки що
  спираються на глобальні `APP__JIRA__TOKEN` і `APP__TC__TOKEN`.

## Decisions

### D1 — Auth: JWT Bearer + таблиця `api_users` (bcrypt password_hash)

**Вибрано:** користувачі зберігаються в новій таблиці `api_users` із
bcrypt-хешем пароля. Login — `SELECT FROM api_users WHERE username = ?
AND is_active = TRUE`, далі `passlib.bcrypt.verify`. JWT — HS256 із
`APP__API__JWT_SECRET`, TTL `APP__API__JWT_TTL_HOURS` (дефолт 24h).

**Чому таблиця, а не env-bcrypt:**

- Multi-user без рефакторингу (можна заводити нового через CLI/seed).
- Кожен користувач має власний `worker_key` (`Jira key`) — JWT claim
  `worker_key` йде з таблиці, не з `settings.current_user`. Це робить
  `settings.current_user` legacy-fallback-ом для CLI/notebook-сценаріїв.
- Ротація паролів і деактивація — звичайний UPDATE, не правка `.env`.

**Альтернативи (відкинуто):**

- *HTTP Basic Auth* — токен у кожному запиті, важко ротувати.
- *Session cookie + Redis* — Redis не у стеку.
- *OAuth/Keycloak* — overkill.
- *env-bcrypt single user* — погана дорога на multi-user, паролі в `.env`.

**Бібліотеки:** `python-jose[cryptography]` для JWT (HS256), `passlib[bcrypt]`
для хешу пароля. `pyjwt` ок як заміна `python-jose`, якщо команда не хоче
`cryptography`.

**Конфіг (нові змінні):**

```
APP__API__HOST=0.0.0.0
APP__API__PORT=8000
APP__API__JWT_SECRET=<random-64-bytes-hex>
APP__API__JWT_TTL_HOURS=24
APP__API__CORS_ORIGINS=http://localhost:3000,https://app.example.com
```

`JWT_SECRET` MUST бути непорожнім — інакше app падає на старті. У токен
кладемо `sub = api_users.username`, `user_id = api_users.id`, `worker_key =
api_users.worker_key`, `exp`, `iat`.

**Бутстрап користувачів:** цей change **НЕ** створює користувачів
автоматично. Перший і всі наступні юзери заводяться через окрему
backend-консольну команду, що буде додана у наступній зміні
(`add-user-management-cli`). На етапі цієї зміни — ручний INSERT через
PyCharm DataGrip (із bcrypt-хешем, згенерованим однією Python-командою).
Інструкція — в `api-reference.md`. API стартує і працює з порожньою
таблицею (login завжди 401, поки не з'явиться перший рядок).

**Схема `api_users`** (нова alembic-ревізія):

```sql
CREATE TABLE api_users
(
    id            SERIAL PRIMARY KEY,
    username      VARCHAR     NOT NULL UNIQUE,
    password_hash VARCHAR     NOT NULL, -- bcrypt
    worker_key    VARCHAR NULL,         -- Jira key для sync-trigger-ів
    is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### D2 — Структура `src/api/`

```
src/api/
├── __init__.py
├── app.py                # FastAPI() factory, CORS, lifespan, include_routers
├── deps.py               # Depends-функції: get_db, get_current_user, get_settings
├── auth.py               # login/refresh endpoints, JWT codec, password hash
├── schemas/              # Pydantic response/request моделі
│   ├── auth.py
│   ├── tc_projects.py
│   ├── jr_projects.py
│   ├── sync_status.py
│   ├── sync_triggers.py
│   └── common.py         # PeriodRequest, спільні error-моделі
└── routers/
    ├── auth.py           # POST /auth/login, POST /auth/refresh, GET /auth/me
    ├── health.py         # GET /healthz (без auth)
    ├── tc_projects.py    # GET /tc-projects, PATCH /tc-projects/{id}
    ├── jr_projects.py    # GET /jr-projects
    ├── sync_status.py    # GET /worklog-sync-tasks, GET /tc-entries/untracked
    └── sync_triggers.py  # POST /sync/...
```

Точка запуску: `python -m src.api` або `uvicorn src.api.app:app --reload`.
Допоміжний `run_api.py` у корені — опційно.

### D3 — Sync triggers: синхронне виконання + опційний `?background=true` + persistent jobs

**Вибрано:** **кожен** виклик sync-endpoint-а (синхронний чи в `BackgroundTasks`)
створює рядок у `api_jobs` із статусом `running`, payload-ом, `created_by`.
Після успішного завершення — `UPDATE status = needs_verification, result =
<counts>, finished_at = now()`. На виключенні — `UPDATE status = failed,
error = <text>, finished_at = now()`.

- За дефолтом запит виконується синхронно: відповідь `200 OK` містить
  `{job_id, status: "needs_verification", result: {...}}`.
- `?background=true` — `202 Accepted` із `{job_id, status: "running"}`.
  Клієнт пуллить `GET /api-jobs/{id}`.

Лайфсайкл `api_jobs.status` — у `D8`.

**Альтернативи:**

- *Тільки sync без api_jobs* — простіше, але немає аудиту, не можна
  перевірити що відбулась синхронізація постфактум.
- *Celery + Redis* — окрема інфраструктура, overkill зараз.
- *FastAPI WebSocket-стрім* — потребує клієнта, що тримає сокет.

**Чому api_jobs:**

1. **Verify-крок**, який просив користувач: ми не вважаємо синк завершеним
   до того, як хтось не подивиться на результат і не натисне «verify».
2. **Аудит**: хто, коли, з якими параметрами запустив. Корисно для
   розбору сторонніх ефектів («чому в таблиці з'явились ці записи?»).
3. **Background-tasks tracking без зовнішньої черги**: статус читається
   звідки треба, без Redis.

### D4 — Read endpoints із параметром періоду

Усі стат-endpoint-и (`/worklog-sync-tasks`, `/tc-entries/untracked`,
`/tc-projects` із entries-counters, `/jr-projects` із issues-counters)
приймають `?start=YYYY-MM-DD&end=YYYY-MM-DD` query-параметри. Дефолт —
поточний місяць (на сервері), щоб «дай мені швидко статус» працювало без
параметрів.

**DTO-стратегія:** нові Pydantic-моделі в `src/api/schemas/*`, що включають
агрегати (`count_entries`, `count_by_status`). Існуючі DTO в
`src/services/*/dto.py` лишаємо без змін — вони описують зовнішні DTO для
HTTP-клієнтів, не API-response.

### D5 — PATCH `/tc-projects/{id}` — partial update із allowed-list

Body: `{is_sync?: bool, issue_key?: str | null}`. Жодні інші поля не
приймаються. Якщо передано порожнє тіло — `400 Bad Request`. Якщо
`tc_projects.id` не існує — `404 Not Found`. Записи коммітяться через
`BaseDAO.update_by_keys` (`key_sync='id'`) або прямим `UPDATE` —
імплементатор обирає простіший шлях.

**Чому PATCH, а не PUT:** оновлюємо лише два прапори, не хочемо випадково
обнулити інші TimeCamp-поля.

### D6 — Залежність на БД через FastAPI `Depends`

```python
async def get_db() -> AsyncSession:
    async with get_async_asession() as db:
        yield db
```

Reuse існуючого контекст-менеджера. Кожен запит → своя сесія, автокоміт на
виході (як вже зроблено в `get_async_asession`).

### D7 — CORS через config (comma-separated origins)

`APP__API__CORS_ORIGINS` — рядок, comma-separated список доменів,
наприклад: `http://localhost:3000,https://app.example.com`. Парситься в
`APIConfig` через `field_validator` у список. Спецзначення `*` (одне) —
відкритий CORS (тільки для локалки). Якщо змінна не задана — дефолт `*`
(локалка).

Конкретні production-домени з'являться у наступних змінах (`add-frontend`).
Зараз — лише механізм конфігурації.

Деплой: `docker-compose` отримує новий сервіс `api` з `uvicorn`. Або
залишаємо локально через `poetry run uvicorn src.api.app:app`.

### D8 — `api_jobs`: лайфсайкл і схема

**Стейт-машина:**

```
[POST /sync/*]
   ↓ INSERT api_jobs(status=running, started_at=now, ...)
   │
   ├─ task succeeds  → UPDATE status=needs_verification, result, finished_at
   │                       │
   │                       └─ POST /api-jobs/{id}/verify
   │                              ↓ UPDATE status=verified, verified_at, verified_by
   │
   └─ task raises    → UPDATE status=failed, error, finished_at
```

- `running` — task запущено, ще не завершено.
- `needs_verification` — task відпрацював без виключень, але користувач ще
  не підтвердив що дані ОК. **Це проміжний стан**, не final.
- `verified` — користувач підтвердив (POST `/api-jobs/{id}/verify`). Final.
- `failed` — task впав на виключенні. Final. Без verify — повтор синку
  створить новий рядок `api_jobs`.

**Схема `api_jobs`** (нова alembic-ревізія):

```sql
CREATE TYPE api_job_status_enum AS ENUM (
    'running', 'needs_verification', 'verified', 'failed'
);

CREATE TABLE api_jobs
(
    id           UUID PRIMARY KEY             DEFAULT gen_random_uuid(),
    trigger_name VARCHAR             NOT NULL, -- 'sync.timecamp.entries'
    status       api_job_status_enum NOT NULL DEFAULT 'running',
    payload      JSONB NULL,                   -- request body / query params
    result       JSONB NULL,                   -- counts після успіху
    error        TEXT NULL,                    -- error message при failed
    created_by   VARCHAR             NOT NULL, -- api_users.username
    verified_by  VARCHAR NULL,                 -- api_users.username
    started_at   TIMESTAMPTZ         NOT NULL DEFAULT now(),
    finished_at  TIMESTAMPTZ NULL,
    verified_at  TIMESTAMPTZ NULL,

    -- soft links без FK (відповідно до конвенції проекту, schema.md §1)
    CHECK (verified_at IS NULL OR status = 'verified'),
    CHECK (finished_at IS NULL OR status != 'running'
)
    );

CREATE INDEX ix_api_jobs_status ON api_jobs (status);
CREATE INDEX ix_api_jobs_trigger_name ON api_jobs (trigger_name);
CREATE INDEX ix_api_jobs_started_at ON api_jobs (started_at);
```

**Auth для verify:** будь-який валідний токен. Версія з RBAC «лише той,
хто запустив, або admin» — окрема зміна.

**Очистка старих jobs:** TTL/cron поки не робимо. Якщо таблиця почне
рости — додамо `cleanup-old-api-jobs` зміною.

## Risks / Trade-offs

- **Довгий sync блокує HTTP-запит.** → Опційний `?background=true` через
  `BackgroundTasks`; client пуллить `GET /api-jobs/{id}`. Документуємо в
  OpenAPI.
- **JWT secret rotation складна** (всі видані токени інвалідуються). → TTL
  24h обмежує вікно. Версія з rotation і список валідних `kid` — окрема
  зміна.
- **`tc_projects.id` приходить із TimeCamp.** PATCH працює лише з існуючими
  id; якщо проект ще не імпортовано — 404. → Документуємо в OpenAPI; UI
  повинен спершу викликати `/sync/timecamp/projects`.
- **`is_sync=true` для проекту, у якого `tc_projects.issue_key` ще не
  встановлений** — entries без `meta.task` потраплять у `untracked`. → Це
  існуюча поведінка, не нова проблема. Read-endpoint untracked допоможе
  ловити.
- **Chicken-and-egg: API живий, але без юзерів** — після першого деплою
  таблиця `api_users` порожня; жоден `/auth/login` не пройде. → Документуємо
  у `api-reference.md`: запит на ручний INSERT через DataGrip із прикладом
  команди для bcrypt-хешу. Постійний фікс — окрема зміна
  `add-user-management-cli`.
- **`_make_request` у Jira/TimeCamp клієнтах поглинає мережеві помилки і
  повертає `{}`** (див. `docs/technical/integrations/jira.md` §10). Sync-endpoint
  у такій ситуації пише `api_jobs.status = needs_verification` із
  `result.created = 0`. → Користувач помітить на verify-кроці й
  перезапустить синк. Виправлення `_make_request` — окрема зміда
  (`fix-jira-service-bugs`).
- **`needs_verification` jobs можуть накопичуватись**, якщо ніхто не
  верифіковує. → Read-endpoint `GET /api-jobs?status=needs_verification`
  плюс прапор на UI «у тебе X непідтверджених синків» (UI — окрема зміна).
- **api_jobs.payload може містити sensitive дані** (issue keys, period).
  Найгірше — JQL-key list. → Для поточного скоупу прийнятно: тільки
  авторизовані юзери бачать. У production з RBAC — окрема зміна.
- **CORS `*` за дефолтом** — допустимо в локальному dev. Для production
  оператор зобов'язаний задати `APP__API__CORS_ORIGINS`. → Логуємо warning
  на старті, якщо CORS = `*` і `host != localhost`.

## Migration Plan

1. **Залежності:** `poetry add python-jose[cryptography] passlib[bcrypt]`.
2. **Config:** додати `APIConfig` у `src/config.py`, оновити `.env.template`
   (включно з seed-admin змінними і `CORS_ORIGINS`).
3. **Alembic-ревізії:**
    - `api_users` (id, username UNIQUE, password_hash, worker_key, is_active,
      timestamps) — нова таблиця.
    - `api_job_status_enum` + `api_jobs` (uuid PK, status enum, payload,
      result, error, created_by, verified_by, timestamps, чек-констрейнти).
    - Перших юзерів **НЕ створюємо** автоматично — інструкція по ручному
      INSERT піде в `api-reference.md`. Повноцінне управління користувачами —
      окрема наступна зміна `add-user-management-cli`.
4. **ORM-моделі та DAO** для `APIUser`, `APIJob` — в `src/models/` і
   `src/dao/` за тими ж конвенціями (snake_case, без FK).
5. **Скеффолд `src/api/`:** структура D2.
6. **Auth:** login/me/refresh (читає з `api_users`).
7. **Capability `api-jobs`:** middleware/контекстний хелпер, що обгортає
   sync-trigger у `running → needs_verification/failed` lifecycle; роутер
   `/api-jobs` (list/get/verify).
8. **Read endpoints:** tc-projects → jr-projects → worklog-sync-tasks →
   untracked.
9. **Sync triggers:** TimeCamp → Jira → Worklog sync tasks. Кожен інтегрує
   api_jobs-обгортку з кроку 7.
10. **PATCH /tc-projects/{id}:** після read-endpoint.
11. **Documentation:** оновити `docs/technical/database/schema.md` і
    `database/erd.md` із новими `api_users`, `api_jobs` (правило з SKILL
    `db-introspection` §8). Створити `docs/technical/api-reference.md`.
12. **Manual QA через `/docs`** + один smoke-тест по кожному endpoint.
13. **Rollback:**
    - `alembic downgrade -<rev>` на дві ревізії (api_jobs + api_users).
    - Видалити `src/api/`, прибрати залежності, видалити `APIConfig`.
    - Існуюча CLI/notebook-робота — без змін.

## Resolved Decisions (раніше Open Questions)

- ✅ **Authoritative source для passwords:** таблиця `api_users` (D1).
  Multi-user-ready з самого початку.
- ✅ **Background-task результати:** persistent `api_jobs` з проміжним
  статусом `needs_verification` (D3, D8). Кожен виклик sync-endpoint-а
  створює рядок; синхронізація вважається завершеною тільки після
  ручного verify.
- ✅ **CORS origins:** comma-separated через `APP__API__CORS_ORIGINS` (D7).
  Конкретні production-домени — наступні зміни (`add-frontend`).
- ✅ **Rate-limiting:** не робимо в цьому change.
