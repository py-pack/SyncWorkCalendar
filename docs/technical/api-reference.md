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
# 0. Залежності
uv sync

# 1. БД
docker compose up -d db
uv run alembic upgrade head          # має дати head ef2c7288bbb0

# 2. JWT-секрет (одноразово в .env)
uv run python -c 'import secrets; print(secrets.token_hex(32))'
# скопіювати у APP__API__JWT_SECRET в .env

# 3. Старт
uv run run_api.py
# або:
uv run uvicorn src.api.app:app --reload
```

OpenAPI: `http://localhost:8000/docs`. Health-check без авторизації:
`http://localhost:8000/healthz`.

## 2. Перший користувач

API **не створює юзерів автоматично** — ні через endpoint, ні на старті.
Юзери заводяться CLI-командою `add_user` (деталі — [cli.md](cli.md)):

```sh
uv run python -m src.cli add_user --username admin --worker-key TEAM-1
# або: make add-user   (питатиме username/password інтерактивно)
```

Команда сама хешує пароль (`bcrypt`, формат `$2b$`) і перевіряє дубль по
`username`. Ручний `INSERT` більше не потрібен.

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

### Google-вхід (`POST /auth/google`)

Альтернативний спосіб довести особу — Google. Видає **той самий** JWT, що й
логін/пароль (ті самі claims); решта сесії однакова. Реєстрації немає —
лише зіставлення з наявним `api_users` за e-mail.

```
client                                   api
  │  POST /auth/google {credential|code}   │
  │ ─────────────────────────────────────▶ │  верифікація в Google (google-auth):
  │                                         │   підпис JWKS, aud==GOOGLE_CLIENT_ID, iss, exp,
  │                                         │   email_verified; для {code} — обмін у Google
  │                                         │  get_by_email(lower-case, тільки is_active)
  │  200 {access_token, expires_in}         │
  │ ◀───────────────────────────────────── │
```

- Тіло — **рівно одне** з полів: `{credential}` (Google **ID-token**: One Tap /
  GIS credential-режим) або `{code}` (auth-**code** з popup-флоу). Обидва поля
  або жодного → `422`.
- `{code}` бекенд обмінює в Google на токени (`redirect_uri=postmessage`,
  потрібен `GOOGLE_CLIENT_SECRET`) і далі верифікує отриманий ID-token.
- Невідомий/неактивний e-mail **або** будь-яка невдача верифікації →
  `401 {detail: "account not found"}` (однакова відповідь, без розрізнення).
  Рядок в `api_users` не створюється.
- `GOOGLE_CLIENT_ID` порожній → `503 "google sign-in is not configured"`
  (не `500`). `{code}` без `GOOGLE_CLIENT_SECRET` →
  `503 "google code flow is not configured"`. Логін/пароль працює незалежно.
- Конфіг (backend-env): `APP__API__GOOGLE_CLIENT_ID` (публічний, його ж віддаємо
  фронту як `VITE_GOOGLE_CLIENT_ID`), `APP__API__GOOGLE_CLIENT_SECRET` (лише на
  беку). Authorized JS origin фронта для GIS/One Tap — `https://sync.dev`.
- Передумова: у відповідного `api_users` має бути заповнений `email` (UNIQUE,
  nullable). Поки немає Users CRUD — через CLI/ручний `UPDATE`.

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
- `POST /auth/google` (Google credential/code; `503` якщо не налаштований)
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
- `PATCH /jr-projects/{id}` — body `{is_watched?}` (`extra=forbid`; лише локальний
  прапор, у Jira нічого не пишемо; `404` на відсутній)
- `GET /jr-issues?project_id=` — задачі Jira з локальної БД (read-only)
- `GET /worklog-sync-tasks?start=&end=&status=`
- `GET /tc-entries/untracked?start=&end=`
- **Users CRUD** (`api-users-management`):
  - `GET /users` — список (без `password_hash`)
  - `POST /users` — body `{username, email, worker_key?, password?}`; invite без
    пароля → `password_hash NULL`, вхід через Google за `email`; дубль
    `email`/`username` → `409`
  - `PATCH /users/{id}` — body `{username?, worker_key?, is_active?}`; `404`/`409`
  - `DELETE /users/{id}` — `204`; `404` на відсутній
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

- **Управління користувачами** — базовий CRUD уже є (`GET/POST/PATCH/DELETE
  /users`, capability `api-users-management`, invite без пароля → Google-вхід).
  Лишилось окремою зміною: set-password через API, CLI list/deactivate
  (`add-user-management-cli`).
- **TTL/cron для `api_jobs`** — `add-api-jobs-cleanup`.
- **RBAC**: усі `api_users` мають однакові права, verify може робити
  будь-хто з валідним токеном. Обмеження «лише admin / автор» — `add-rbac`.
- **Per-user OAuth-токени** на Jira/TimeCamp — окрема майбутня зміна;
  зараз `APP__JIRA__TOKEN` і `APP__TC__TOKEN` глобальні.
- **Frontend SPA** — `add-frontend`; тут лише backend + OpenAPI.
- **Async-черга / Celery** — не потрібна; sync виконується синхронно або
  через FastAPI `BackgroundTasks` (`?background=true`).
