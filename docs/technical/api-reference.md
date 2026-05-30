# HTTP API Reference

Технічна довідка по REST API проєкту. Imple­ment-фаза зміни
`add-rest-api`. OpenAPI / Swagger UI віддає сам FastAPI на
`/docs`, `/redoc`, `/openapi.json` — це джерело правди для контрактів.
Цей файл фіксує **операційні нюанси**: як підняти, як завести юзера, як
читати lifecycle `api_jobs`, як працює auth.

> Спеки вимог — у `openspec/changes/add-rest-api/specs/` (поки не
> архівовано) або, після `/openspec-archive-change`, у `openspec/specs/`.

## 1. Як підняти

```sh
# 1. БД
docker compose up -d db
poetry run alembic upgrade head      # має дати head ef2c7288bbb0

# 2. JWT-секрет (одноразово в .env)
python -c 'import secrets; print(secrets.token_hex(32))'
# скопіювати у APP__API__JWT_SECRET в .env

# 3. Старт
poetry run python run_api.py
# або:
poetry run uvicorn src.api.app:app --reload
```

OpenAPI: `http://localhost:8000/docs`. Health-check без авторизації:
`http://localhost:8000/healthz`.

## 2. Перший користувач

API **не створює юзерів автоматично** — ні через endpoint, ні на старті.
До появи зміни `add-user-management-cli` юзери заводяться ручним INSERT.

```sh
# 1) bcrypt-хеш пароля
poetry run python -c "from passlib.hash import bcrypt; print(bcrypt.hash('your-strong-password'))"

# 2) INSERT через PyCharm DataGrip / psql
```

```sql
INSERT INTO api_users (username, password_hash, worker_key, is_active, created_at, updated_at)
VALUES ('admin', '<bcrypt-хеш з кроку 1>', '<your-jira-key>', TRUE, now(), now());
```

`worker_key` — твій Jira key. Для логіну, `GET /auth/me`,
`GET /tc-projects`, верифікації — необовʼязковий, можна `NULL`. Без нього
ламаються лише `POST /sync/jira/worklogs` і
`POST /sync/worklog-tasks/push-to-tempo` (повертають `400` з
`{detail: "user has no worker_key configured"}`).

## 3. Auth flow

```
client                                  api
  │  POST /auth/login {username,password}  │
  │ ───────────────────────────────────── ▶│  SELECT api_users WHERE username = ?
  │                                        │  bcrypt.verify(password, password_hash)
  │  200 {access_token, expires_in}        │
  │ ◀──────────────────────────────────── │
  │  Authorization: Bearer <token>         │
  │ ───────────────────────────────────── ▶│  decode + SELECT api_users (re-check is_active)
  │  200 ... або 401                       │
```

- TTL токена — `APP__API__JWT_TTL_HOURS` (дефолт 24 год).
- Login повертає однаковий `401 Invalid credentials` для wrong password /
  unknown user / inactive user.
- Refresh (`POST /auth/refresh`) — приймає валідний токен у заголовку,
  повертає новий із новим `exp`; для прострочених токенів — `401`.
- Деактивований юзер не може ні логінитись, ні refresh-итись.

JWT claims: `sub` (username), `user_id`, `worker_key`, `iat`, `exp`.

## 4. `api_jobs` lifecycle

Кожен `POST /sync/**` створює рядок у `api_jobs`. State machine:

```
running ──success──▶ needs_verification ──POST /api-jobs/{id}/verify──▶ verified
   │
   └──exception─────▶ failed
```

- `verified`, `failed` — final.
- `running → verified` напряму **неможливо** — verify працює лише на
  `needs_verification` (інакше `409 Conflict`).
- Повторити синк після `failed` — викликати той самий endpoint; буде нова
  job-row.

Поля рядка:

| поле          | коли заповнюється                       |
| ------------- | --------------------------------------- |
| `started_at`  | відразу при INSERT (`status=running`)   |
| `finished_at` | при переході в `needs_verification` / `failed` |
| `verified_at` | при `POST /api-jobs/{id}/verify`        |
| `payload`     | request body або query на старті        |
| `result`      | counts після успіху                     |
| `error`       | `str(exception)` при `failed`           |
| `created_by`  | `sub` з JWT (`username`)                |
| `verified_by` | `sub` з JWT того, хто натиснув verify   |

## 5. Endpoint-и

Повний контракт — у Swagger UI. Тут — карта:

### Public
- `GET /healthz`
- `POST /auth/login`
- `POST /auth/refresh` (приймає Bearer)
- `GET /docs`, `/redoc`, `/openapi.json`

### Authenticated
- `GET /auth/me`
- `GET /api-jobs?status=&trigger_name=&start=&end=&limit=&offset=`
- `GET /api-jobs/{id}`
- `POST /api-jobs/{id}/verify`
- `GET /tc-projects?start=&end=` — список TC-проектів із `entries_count`
- `PATCH /tc-projects/{id}` — body `{is_sync?, issue_key?}` (`extra=forbid`)
- `GET /jr-projects`
- `GET /worklog-sync-tasks?start=&end=&status=`
- `GET /tc-entries/untracked?start=&end=`
- `POST /sync/timecamp/projects`
- `POST /sync/timecamp/entries` body `{start, end}`
- `POST /sync/jira/projects`
- `POST /sync/jira/issues` body `{keys: [str]}`
- `POST /sync/jira/worklogs` body `{start, end}` *(worker_key з JWT)*
- `POST /sync/worklog-tasks/prepare` body `{start, end}`
- `POST /sync/worklog-tasks/resolve-issues` body `{start, end}`
- `POST /sync/worklog-tasks/push-to-tempo` body `{start, end}` *(worker_key з JWT)*

Усі sync-endpoint-и приймають `?background=true` — повертають `202` з
`{job_id, status: "running"}`. Без прапора — `200` із
`{job_id, status: "needs_verification", result}`.

## 6. CORS

`APP__API__CORS_ORIGINS` — comma-separated список origin-ів, наприклад:

```
APP__API__CORS_ORIGINS=http://localhost:3000,https://app.example.com
```

Дефолт — `*` (відкрито для локалки). На non-local `APP__API__HOST` з `*`
у CORS — у лог йде warning на старті.

## 7. Що поза цією зміною

- **Управління користувачами** (create/list/deactivate/set-password) —
  окрема майбутня зміна `add-user-management-cli`.
- **TTL/cron для `api_jobs`** — `add-api-jobs-cleanup`.
- **RBAC**: усі `api_users` мають однакові права, verify може робити
  будь-хто з валідним токеном. Обмеження «лише admin / автор» — `add-rbac`.
- **Per-user OAuth-токени** на Jira/TimeCamp — окрема майбутня зміна;
  зараз `APP__JIRA__TOKEN` і `APP__TC__TOKEN` глобальні.
- **Frontend SPA** — `add-frontend`; тут лише backend + OpenAPI.
- **Async-черга / Celery** — не потрібна; sync виконується синхронно або
  через FastAPI `BackgroundTasks` (`?background=true`).
