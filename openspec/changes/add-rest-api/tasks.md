## 1. Залежності та конфігурація

- [x] 1.1 `poetry add python-jose[cryptography] passlib[bcrypt]` (або
  `pyjwt` як заміна `python-jose`, якщо команда проти cryptography).
  *Додатково:* `poetry add greenlet` — обовʼязковий runtime-deps для
  `sqlalchemy.async` на Python 3.13.
- [x] 1.2 Розширити `src/config.py`: додати клас `APIConfig` (host, port,
  jwt_secret, jwt_ttl_hours, cors_origins). Підключити у `Settings.api`
- [x] 1.3 `APIConfig.cors_origins`: `field_validator(mode='before')`, що
  перетворює comma-separated рядок у `list[str]`; спецзначення `*`
  залишити як список з одного елемента. Використано
  `Annotated[list[str], NoDecode]`, щоб pydantic-settings не парсив
  значення як JSON.
- [x] 1.4 Оновити `.env.template` змінними `APP__API__*` із поясненнями
- [x] 1.5 Валідація на старті: якщо `APP__API__JWT_SECRET` порожній —
  `RuntimeError`. Перенесено у `Settings.require_api_ready()`, що
  викликається `lifespan` FastAPI і `run_api.py` — щоб CLI/notebook без
  API могли працювати з порожнім секретом.

## 2. Alembic-міграції та ORM-моделі

- [x] 2.1 `src/models/api_user.py`: модель `APIUser` (`__tablename__ =
      'api_users'`) — `username UNIQUE NOT NULL`, `password_hash`,
  `worker_key NULL`, `is_active DEFAULT TRUE`, `created_at`,
  `updated_at`. Stamp-листенер `_stamp_api_user_timestamps`.
- [x] 2.2 `src/models/api_job.py`: модель `APIJob` (`__tablename__ =
      'api_jobs'`) — `id UUID PK gen_random_uuid()`, `trigger_name`,
  `status Enum(APIJobStatusEnum)`, `payload JSONB`, `result JSONB`,
  `error TEXT NULL`, `created_by`, `verified_by`, `started_at`,
  `finished_at`, `verified_at`. CHECK-constraints.
- [x] 2.3 Енам `APIJobStatusEnum` із значеннями `running`,
  `needs_verification`, `verified`, `failed` у тому ж модулі (за
  аналогією до `StatusTaskEnum`)
- [x] 2.4 + 2.5 Одна `alembic revision --autogenerate -m
      "add_api_layer_tables"` створила і `api_users`, і `api_jobs` (+ enum
      і 3 індекси). Перейменовано в
      `2026_05_12_1656-ef2c7288bbb0_add_api_layer_tables.py`. Виправлено
      `server_default` UUID на `sa.text("gen_random_uuid()")`.
- [x] 2.6 Запустити `alembic upgrade head` локально. Поточний head —
      `ef2c7288bbb0`.
- [x] 2.7 Оновити `docs/technical/database/schema.md` та
      `database/erd.md` — додано секцію «API-домен», новий enum
      `api_job_status_enum`, sequence `api_users_id_seq`, soft links,
      state-machine у ERD.
- [x] 2.8 `src/dao/api_user_dao.py`: `APIUserDAO` (`get_by_username`,
      `count_active`)
- [x] 2.9 `src/dao/api_job_dao.py`: `APIJobDAO` (`create_running`,
      `mark_needs_verification`, `mark_failed`, `mark_verified`,
      `list_filtered`, `get_by_id`)

## 3. Скеффолд `src/api/`

- [x] 3.1 Створити теку `src/api/` із `__init__.py` (уже була, порожній
      `__init__.py` лишений)
- [x] 3.2 `src/api/app.py`: `create_app()` factory, `lifespan` з
      `settings.require_api_ready()`, CORS-middleware, exception
      handler-и для `SQLAlchemyError` (500) і `RequestException` (502),
      підключення всіх роутерів. Експорт `app = create_app()`.
- [x] 3.3 `src/api/deps.py`: `get_db()` (yield із `async_session_maker`),
      `get_current_user()` (декодує JWT + re-read `api_users` для
      is_active), `get_settings()`, dataclass `CurrentUser`.
- [x] 3.4 `src/api/schemas/`: `auth.py`, `common.py`
      (`PeriodQuery`, `PeriodBody`, `BackgroundQuery`, `HealthResponse`,
      `ErrorResponse`, `JobRefResponse`).
- [x] 3.5 `src/api/routers/health.py`: `GET /healthz` → `{status: "ok"}`
- [x] 3.6 Точка запуску — `run_api.py` у корені

## 4. Capability `api-auth`

- [x] 4.1 `src/api/auth.py`: `verify_password`, `hash_password`,
      `create_access_token`, `decode_access_token`, `TokenDecodeError`.
- [x] 4.2 `src/api/routers/auth.py`: `POST /auth/login`, `POST /auth/refresh`,
      `GET /auth/me`. Login дає однаковий `401 Invalid credentials` для
      wrong pwd / unknown user / inactive.
- [x] 4.3 JWT claims: `sub`, `user_id`, `worker_key`, `exp`, `iat`. На
      refresh — `get_current_user` ре-перевіряє `is_active` із БД.
- [x] 4.4 Жодного user-creation endpoint не існує.
- [ ] 4.5 Smoke-test через `/docs` — **залишається для ручного QA** (фаза 11).

## 5. Capability `api-jobs`

- [x] 5.1 `src/api/schemas/api_jobs.py`: `APIJobSummary`, `APIJobDetail`,
      `APIJobListResponse`, `APIJobStatusLiteral`
- [x] 5.2 `src/api/routers/api_jobs.py`: `GET /api-jobs` (фільтри
      `status`, `trigger_name`, `start`, `end`, `limit`, `offset`),
      `GET /api-jobs/{id}`, `POST /api-jobs/{id}/verify`
- [x] 5.3 Verify-endpoint: атомарна перевірка в `APIJobDAO.mark_verified`;
      терміналі стани → 409.
- [x] 5.4 `src/api/jobs_wrapper.py`: `@asynccontextmanager run_job(...)`,
      що тримає **окрему сесію** для audit-row.

## 6. Capability `api-tc-projects-management`

- [x] 6.1 `src/api/schemas/tc_projects.py`: `TCProjectResponse`,
      `TCProjectPatchRequest` (`extra="forbid"`, regex на `issue_key`)
- [x] 6.2 `src/api/routers/tc_projects.py`: `GET /tc-projects`
      (з `entries_count` — задача 7.2 склеєна сюди), `PATCH /tc-projects/{id}`
- [x] 6.3 PATCH: `exclude_unset` для пустого тіла → 400; 404 на відсутній id;
      оновлення двох полів одним flush.
- [x] 6.4 Reuse `TCProjectDAO.find` (через `BaseDAO`).

## 7. Capability `api-sync-status`

- [x] 7.1 `src/api/schemas/sync_status.py`: `JRProjectWithCount`,
      `WorklogSyncTaskItem`, `WorklogSyncTasksResponse`, `UntrackedEntry`
- [x] 7.2 `GET /tc-projects` — entries_count через join `tc_entries` за
      період (склеєно з §6).
- [x] 7.3 `src/api/routers/jr_projects.py`: `GET /jr-projects` із count issues.
      Урахована typo моделі `is_archved`.
- [x] 7.4 `src/api/routers/sync_status.py`: `GET /worklog-sync-tasks` —
      summary (агрегація по статусах за період) + items.
- [x] 7.5 `GET /tc-entries/untracked` — `meta IS NULL` AND (`tc_project_id IS NULL`
      OR `tc_projects.issue_key IS NULL`).

## 8. Capability `api-sync-triggers`

- [x] 8.1 `src/api/schemas/sync_triggers.py`: `PeriodBody`,
      `IssuesKeysBody`, `SyncTriggerResponse`
- [x] 8.2 `src/api/routers/sync_triggers.py`: 8 endpoint-ів, кожен обгорнутий
      у `_execute(...)` (sync — `run_job`; bg — INSERT running + UPDATE з
      BackgroundTasks).
- [x] 8.3 Worker_key з JWT для `/sync/jira/worklogs` і
      `/sync/worklog-tasks/push-to-tempo` перевіряється **до** wrapper-а;
      на null → 400.
- [x] 8.4 `?background=true` через `BackgroundTasks` повертає `202` із
      `{job_id, status: "running"}`.
- [x] 8.5 Counters через `func.count()` до/після виклику task.

## 9. Інтеграція з існуючим стеком

- [x] 9.1 `_make_request` поведінка (повертає `{}` на помилку) лишена
      як є — fix йде окремою зміною `fix-jira-service-bugs`. У failure-
      кейсі wrapper позначить job як `needs_verification` із `result.created=0`,
      і користувач помітить на verify-кроці.
- [x] 9.2 Глобальний exception handler у `app.py`:
      `SQLAlchemyError → 500`, `requests.RequestException → 502`.
- [x] 9.3 `WorllogSyncTask.create_worklogs(..., worker=None)` і
      `UpdateJiraTask.update_worklog(..., worker=None)` приймають
      `worker` параметром (fallback на `settings.current_user` для
      notebook). HTTP-роутер передає `current.worker_key` із JWT.

## 10. Документація

- [x] 10.1 `docs/technical/api-reference.md` із розділами «Як підняти»,
      «Перший користувач» (bcrypt + INSERT), «Auth flow», «api_jobs
      lifecycle», «Endpoint-и», «CORS», «Що поза цією зміною».
- [x] 10.2 Посилання на `api-reference.md` в Memory Bank `techContext.md`
      (нова секція «API»).
- [x] 10.3 `systemPatterns.md`: HTTP-шар у схему «main → tasks →
      services/dao» + опис `jobs_wrapper.run_job` + нова state-machine
      `APIJobStatusEnum`.
- [x] 10.4 `progress.md`: відмічено що FastAPI підняли; додано список
      `api_users`/`api_jobs` функцій; перенесено невикористані `pre_update`
      статуси в not-implemented.
- [x] 10.5 `decisinLog.md`: додано D-010 (`api_jobs` із проміжним
      `needs_verification`). D-009 (multi-user-ready) уже був.

## 11. QA через `/docs`

> **Запис на 2026-05-13:** код готовий, QA лишається користувачу.
> Інструкції — у `docs/technical/api-reference.md` §1–2.

- [ ] 11.1 Підняти локально: `docker compose up -d db && alembic upgrade
      head && uvicorn src.api.app:app --reload`
- [ ] 11.2 **Перед стартом QA:** вручну створити тестового юзера через
      DataGrip — `INSERT INTO api_users (username, password_hash,
      worker_key, is_active, created_at, updated_at) VALUES ('admin',
      '<bcrypt>', '<your-jira-key>', TRUE, now(), now());`
- [ ] 11.3 Smoke-test через Swagger UI (`/docs`) кожного endpoint:
  - 11.3.1 `/auth/login` із вручну вставленими credentials → токен →
  `/auth/me`
  - 11.3.2 `GET /tc-projects` → бачимо рядки
  - 11.3.3 `PATCH /tc-projects/{id}` → перевірка через MCP
  - 11.3.4 Sync trigger TimeCamp projects → `GET /api-jobs/{id}`
  показує `status=needs_verification`
  - 11.3.5 `POST /api-jobs/{id}/verify` → `verified`
  - 11.3.6 Worklog sync flow повністю: prepare → resolve → push,
  кожен крок створює окремий `api_jobs` рядок
  - 11.3.7 Failure-сценарій: вимкнути docker з postgres, виклик
  sync-endpoint → `api_jobs.status = failed`, `error` непорожній
  - 11.3.8 Negative-тест: `POST /auth/register` (та інші підозрілі
  пути типу `POST /api-users`) → `404 Not Found`
  - 11.3.9 Empty-table-тест: ще до 11.2 виклик `POST /auth/login` на
  порожній таблиці → `401 Unauthorized`, без 500
- [ ] 11.4 OpenAPI-валідація: переконатися, що всі моделі рендеряться
  коректно (включно з `Optional`, `Literal`, `datetime`, `UUID`,
  `JSONB`)

## 12. Архівація і фоллоу-апи

- [ ] 12.1 `/openspec-archive-change add-rest-api` — переносить у
      `openspec/changes/archive/`, оновлює `openspec/specs/`
- [ ] 12.2 Створити follow-up changes у бекозі (не в цьому скоупі):
  - 12.2.1 **`add-user-management-cli`** — наступна зміна одразу за
  цією. CLI типу `python -m src.api.scripts.users create
        --username ... --worker-key ...` (інтерактивний prompt пароля),
  плюс `users list`, `users deactivate`, `users set-password`.
  Замінює ручний INSERT, на який спирається QA цієї зміни.
  - 12.2.2 `add-frontend` — UI, конкретні CORS-origin-и
  - 12.2.3 `add-api-jobs-cleanup` — TTL/cron для старих `api_jobs`
  - 12.2.4 `add-rbac` — ролі, обмеження verify «лише admin або
  автор»
  - 12.2.5 `fix-jira-service-bugs` — copy-paste bug у `search_issues`,
  пагінація, екранування JQL
  - 12.2.6 `cleanup-naming-typos` — `is_archved`, `jr_issues_id`,
  `WorllogSyncTask`, `serch_worklogs_by_user`
