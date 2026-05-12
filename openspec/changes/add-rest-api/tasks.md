## 1. Залежності та конфігурація

- [ ] 1.1 `poetry add python-jose[cryptography] passlib[bcrypt]` (або
  `pyjwt` як заміна `python-jose`, якщо команда проти cryptography)
- [ ] 1.2 Розширити `src/config.py`: додати клас `APIConfig` (host, port,
  jwt_secret, jwt_ttl_hours, cors_origins). Підключити у `Settings.api`
- [ ] 1.3 `APIConfig.cors_origins`: `field_validator(mode='before')`, що
  перетворює comma-separated рядок у `list[str]`; спецзначення `*`
  залишити як список з одного елемента
- [ ] 1.4 Оновити `.env.template` змінними `APP__API__*` із поясненнями
- [ ] 1.5 Валідація на старті: якщо `APP__API__JWT_SECRET` порожній —
  `RuntimeError` у `Settings` post-init (Pydantic `model_validator`)

## 2. Alembic-міграції та ORM-моделі

- [ ] 2.1 `src/models/api_user.py`: модель `APIUser` (`__tablename__ =
      'api_users'`) — `username UNIQUE NOT NULL`, `password_hash`,
  `worker_key NULL`, `is_active DEFAULT TRUE`, `created_at`,
  `updated_at`
- [ ] 2.2 `src/models/api_job.py`: модель `APIJob` (`__tablename__ =
      'api_jobs'`) — `id UUID PK gen_random_uuid()`, `trigger_name`,
  `status Enum(APIJobStatusEnum)`, `payload JSONB`, `result JSONB`,
  `error TEXT NULL`, `created_by`, `verified_by`, `started_at`,
  `finished_at`, `verified_at`. CHECK-constraints (`verified_at IS
      NULL OR status='verified'`, `finished_at IS NULL OR status !=
      'running'`)
- [ ] 2.3 Енам `APIJobStatusEnum` із значеннями `running`,
  `needs_verification`, `verified`, `failed` у тому ж модулі (за
  аналогією до `StatusTaskEnum`)
- [ ] 2.4 `alembic revision --autogenerate -m "add_api_users_table"` —
  перевірити, що autogen виловив `api_users`
- [ ] 2.5 `alembic revision --autogenerate -m "add_api_jobs_table"` —
  перевірити, що автоген створив enum-тип + таблицю + 3 індекси
  (`status`, `trigger_name`, `started_at`)
- [ ] 2.6 Запустити `alembic upgrade head` локально + звірити через MCP
  `mcp__pycharm__get_database_object_description`
- [ ] 2.7 **Оновити `docs/technical/database/schema.md` та
  `database/erd.md`** із новими таблицями і enum-ом — окрема секція
  «API-домен». Це частина того ж коміту/PR (правило `db-introspection`
  §8)
- [ ] 2.8 `src/dao/api_user_dao.py`: `APIUserDAO` (наслідує `BaseDAO`,
  `model = APIUser`), додатково `get_by_username(db, username)`,
  `count_active(db)`
- [ ] 2.9 `src/dao/api_job_dao.py`: `APIJobDAO`, методи `create_running`,
  `mark_needs_verification`, `mark_failed`, `mark_verified`,
  `list_filtered`, `get_by_id`

## 3. Скеффолд `src/api/`

- [ ] 3.1 Створити теку `src/api/` із `__init__.py`
- [ ] 3.2 `src/api/app.py`: `FastAPI()`-factory, `lifespan`,
  CORS-middleware із `settings.api.cors_origins`, підключення всіх
  роутерів. Експорт `app = create_app()`. Стартуємо навіть із порожньою
  таблицею `api_users` — без падінь
- [ ] 3.3 `src/api/deps.py`: `get_db()` (yield із `get_async_asession()`),
  `get_current_user()` (декодує JWT, читає `api_users` для
  підтвердження `is_active`), `get_settings()`
- [ ] 3.4 `src/api/schemas/`: модулі `auth.py`, `common.py`
  (`PeriodRequest`, `BackgroundQuery`, `JobResponse`, error-моделі)
- [ ] 3.5 `src/api/routers/health.py`: `GET /healthz` → `{status: "ok"}`
  (публічний)
- [ ] 3.6 Точка запуску — `run_api.py` у корені з
  `uvicorn.run("src.api.app:app", ...)` або `python -m src.api`

## 4. Capability `api-auth`

- [ ] 4.1 `src/api/auth.py`: функції `verify_password`, `hash_password`,
  `create_access_token`, `decode_access_token`
- [ ] 4.2 `src/api/routers/auth.py`: `POST /auth/login`, `POST /auth/refresh`,
  `GET /auth/me`. Login робить `APIUserDAO.get_by_username` +
  `verify_password`; на провал — однакова відповідь 401 для всіх трьох
  сценаріїв (wrong pwd / unknown user / inactive)
- [ ] 4.3 JWT claims: `sub`, `user_id`, `worker_key`, `exp`, `iat`. На
  refresh — перечитати `is_active` з БД (деактивований юзер не може
  рефрешитись)
- [ ] 4.4 Жодного user-creation endpoint у роутерах. `POST /auth/register`,
  `POST /api-users` тощо MUST не існувати — щоб майбутній CLI лишався
  єдиним джерелом створення
- [ ] 4.5 Smoke-test через `/docs`: вручну (через DataGrip) додати тестового
  юзера → `/auth/login` → токен → `/auth/me` → перевірка
  `Authorization: Bearer ...` на захищеному роуті

## 5. Capability `api-jobs`

- [ ] 5.1 `src/api/schemas/api_jobs.py`: `APIJobSummary`, `APIJobDetail`,
  `APIJobListResponse`, `APIJobStatusQuery` (Literal enum)
- [ ] 5.2 `src/api/routers/api_jobs.py`: `GET /api-jobs` (фільтри
  `status`, `trigger_name`, `start`, `end`, `limit`, `offset`),
  `GET /api-jobs/{id}`, `POST /api-jobs/{id}/verify`
- [ ] 5.3 Verify-endpoint: атомарна перевірка `status =
      needs_verification` + UPDATE → `verified, verified_at, verified_by`;
  на інші стани — `409 Conflict`
- [ ] 5.4 `src/api/jobs_wrapper.py`: async-контекстний менеджер
  `run_job(trigger_name, payload, user, db)`, що:
  - на enter — INSERT `api_jobs` зі `status=running`
  - на normal-exit — UPDATE `needs_verification + result`
  - на exception — UPDATE `failed + error`, потім re-raise
  - повертає `job_id`, який endpoint включає у response

## 6. Capability `api-tc-projects-management`

- [ ] 6.1 `src/api/schemas/tc_projects.py`: `TCProjectResponse`,
  `TCProjectPatchRequest` (тільки `is_sync?`, `issue_key?`, з
  `extra="forbid"` і regex-валідацією `issue_key`)
- [ ] 6.2 `src/api/routers/tc_projects.py`: `GET /tc-projects` (без
  entries-counts поки що), `PATCH /tc-projects/{id}`
- [ ] 6.3 PATCH: дістати запис через `BaseDAO`, перевірити що body
  непорожнє, оновити обрані поля, commit, повернути оновлений
  `TCProjectResponse`
- [ ] 6.4 Reuse: знайти `TCProjectDAO`; якщо потрібен `get_by_id` —
  додати або використати `BaseDAO.find`

## 7. Capability `api-sync-status`

- [ ] 7.1 `src/api/schemas/sync_status.py`: `TCProjectWithCount`,
  `JRProjectWithCount`, `WorklogSyncTaskSummary`, `UntrackedEntry`,
  `PeriodFilter` (валідація `start <= end`)
- [ ] 7.2 `GET /tc-projects` (додати в існуючий роутер): join із
  `tc_entries` за період + groupby count
- [ ] 7.3 `src/api/routers/jr_projects.py`: `GET /jr-projects` із count
  issues
- [ ] 7.4 `src/api/routers/sync_status.py`: `GET /worklog-sync-tasks` —
  reuse `WorklogSyncTaskDAO.get_by_period_and_status`, додати
  агрегуючий запит для `summary`
- [ ] 7.5 `GET /tc-entries/untracked`: SELECT `tc_entries` LEFT JOIN
  `tc_projects` WHERE `tc_entries.meta IS NULL AND
      (tc_projects.issue_key IS NULL OR tc_project_id IS NULL)` за період

## 8. Capability `api-sync-triggers`

- [ ] 8.1 `src/api/schemas/sync_triggers.py`: `PeriodBody {start, end}`,
  `IssuesKeysBody {keys: list[str]}`, `SyncTriggerResponse {job_id,
      status, result?}`, response-варіанти на кожен endpoint
- [ ] 8.2 `src/api/routers/sync_triggers.py`: 8 endpoint-ів, кожен
  обгорнутий у `run_job(...)` wrapper (з §5):
  - 8.2.1 `POST /sync/timecamp/projects` → `TimeCampUpdateTask.update_project()`
  - 8.2.2 `POST /sync/timecamp/entries` → `update_entries(start, end)`
  - 8.2.3 `POST /sync/jira/projects` → `UpdateJiraTask.update_all_projects()`
  - 8.2.4 `POST /sync/jira/issues` → `update_jira_issues(keys)` (validate non-empty до wrapper-а)
  - 8.2.5 `POST /sync/jira/worklogs` → `update_worklog(start, end)`, worker із JWT-claim
  - 8.2.6 `POST /sync/worklog-tasks/prepare` → `WorllogSyncTask.create_task_for_sync(...)`
  - 8.2.7 `POST /sync/worklog-tasks/resolve-issues` → `before_create(...)`
  - 8.2.8 `POST /sync/worklog-tasks/push-to-tempo` → `create_worklogs(...)`, worker із JWT
- [ ] 8.3 Worker_key з JWT: для endpoint-ів 8.2.5 і 8.2.8 перевіряти
  `worker_key IS NOT NULL` ДО wrapper-а; на `null` — `400` без
  створення `api_jobs`
- [ ] 8.4 Опційний `?background=true`: викинути виконання у FastAPI
  `BackgroundTasks`, повернути `202 Accepted` з `{job_id, status:
      "running"}`. Wrapper робить ту саму lifecycle-роботу
- [ ] 8.5 Counters для `result`: helper, що рахує `SELECT COUNT(*)`
  до/після виклику task (простіше за модифікацію DAO)

## 9. Інтеграція з існуючим стеком

- [ ] 9.1 Перевірити, що `_make_request` помилки не валять FastAPI-worker;
  обробка винятків → wrapper переводить `api_jobs` у `failed`,
  HTTP-відповідь `500 Internal Server Error` із `{job_id, detail}`
- [ ] 9.2 Глобальний exception handler у `app.py` для
  `sqlalchemy.exc.SQLAlchemyError` і `requests.RequestException`
- [ ] 9.3 Розділення `settings.current_user` і HTTP worker_key:
  - `WorllogSyncTask.create_worklogs` приймає `worker` параметром
  (рефактор у `src/tasks/worllog_sync_task.py`),
  - або endpoint підставляє worker через локальний contextvar.
  Зафіксувати рішення тут після першої спроби

## 10. Документація

- [ ] 10.1 Створити `docs/technical/api-reference.md` з оглядом
  endpoint-ів, auth flow, `api_jobs` lifecycle і прикладами `curl`.
  Окремий розділ — **«Як завести першого користувача»**: bcrypt-команда
  (`python -c "from passlib.hash import bcrypt; print(bcrypt.hash('...'))"`),
  приклад INSERT-запиту в `api_users` через DataGrip, посилання на
  майбутній `add-user-management-cli`
- [ ] 10.2 Додати посилання на `api-reference.md` у Memory Bank
  `techContext.md` (нова секція «API»)
- [ ] 10.3 Оновити `systemPatterns.md`: додати шар HTTP у схему «main →
  tasks → services/dao» + lifecycle `api_jobs`
- [ ] 10.4 Оновити `progress.md`: відмітити, що FastAPI підняли (раніше
  числився як «не реалізовано»), додати `api_users`/`api_jobs`
- [ ] 10.5 Оновити `decisinLog.md`: записати рішення (1) користувачі в
  таблиці `api_users`, заведення тільки через CLI (наступна зміна);
  (2) `api_jobs` як проміжний verify-крок між `running` і `verified`

## 11. QA через `/docs`

- [ ] 11.1 Підняти локально: `docker compose up -d db && alembic upgrade
      head && uvicorn src.api.app:app --reload`
- [ ] 11.2 **Перед стартом QA:** вручну створити тестового юзера через
  DataGrip — `INSERT INTO api_users (username, password_hash,
      worker_key, is_active) VALUES ('admin', '<bcrypt>', '<your-jira-key>',
      TRUE);`. Команда для генерації хешу — у `api-reference.md` §
  «Перший користувач»
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
