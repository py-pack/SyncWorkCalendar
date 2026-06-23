# System Patterns

## Розкладка монорепо

Код розділено на `api/` (Python-бекенд, пакет `app` — фізично `api/app/`) та
`front/` (Vue 3 + Vite + TS). Docker, `openspec/`, `docs/` і кореневий
`Makefile` — спільні на корені. Деталі — `techContext.md`; рішення про
переїзд `src`→`app` — `decisinLog.md` → D-012.

## Шари

```
front/ (Vue 3 + Vite + TS)   ← SPA: vue-router, Pinia, fetch-клієнт → /api (Vite-проксі)
   │   (також curl, Swagger UI)
   ▼
api/app/api/                 ← FastAPI: app, routers, schemas, deps, auth, jobs_wrapper
   │       └─► run_job(...)  ← context manager → INSERT/UPDATE api_jobs (своя сесія)
   │
api/app/{main.py,…}          ← альтернативна (legacy) точка входу (main.py / main.ipynb)
app/cli/*                    ← argparse-CLI з авто-реєстрацією команд
   │                            (операційні дії; реюз dao/core/auth)
   ▼
app/tasks/*                  ← оркестрація (TimeCamp/Jira/Worklog tasks)
   │
   ├─► app/services/*        ← HTTP-клієнти зовнішніх API + DTO (Pydantic)
   │
   └─► app/dao/*             ← робота з БД через SQLAlchemy AsyncSession
            │
            ▼
       app/models/*          ← SQLAlchemy 2.x Declarative моделі
```

- `app/api/app.py` — `create_app()` factory; `lifespan` валідує
  `APP__API__JWT_SECRET`; включає CORS-middleware і глобальні exception
  handler-и для `SQLAlchemyError` (500) і `requests.RequestException` (502).
- `app/api/jobs_wrapper.run_job(...)` — async-контекстний менеджер навколо
  sync-endpoint-а: `INSERT api_jobs.running` → yield `ctx` → `UPDATE
  needs_verification + ctx.result` на normal-exit / `UPDATE failed + error`
  на exception. Wrapper тримає **окрему сесію**, щоб audit-row лишався
  навіть коли request-сесія відкочується.

- `app/core/db_helper.py` тримає глобальний `async_engine`, `sync_engine`
  і контекст-менеджер `get_async_asession()` (автокоміт на виході, rollback при
  винятку). Клас `DatabaseHelper` лишився як `deprecated`.
- `app/config.py` — `pydantic-settings`, префікс `APP__`, вкладеність через
  `__`. Підвантаження за абсолютними шляхами, пріоритет (від нижчого):
  `api/.env.template` → `<root>/.env` → `api/.env` (реальні env — над усіма).

## DAO-патерн

- `BaseDAO` уніфікує `find/exists/all/sync_all/update_by_keys`.
- `sync_all(db, dto_list)` робить **повну синхронізацію**: створює нові,
  оновлює існуючі та **видаляє** моделі, чий `key_sync` (за замовчуванням `id`)
  відсутній у вхідному `dto_list`. Це безпечно для проектів, але для
  worklog-ів використовується `sync_all_between(...)`, який обмежує вибірку
  періодом, щоб не видалити чужі дані.
- `_sync_dto_with_models` робить `model.fill(**dto.model_dump())` для апдейту
  або `model.create(**dto.model_dump())` для інсерту. Для цього `Base` має
  методи `fill` і `create` (`models/base.py`).
- DAO для join-ів і агрегатів містять додаткові методи: `TCEntriesDAO.get_entries_for_worklogs`,
  `WorklogSyncTaskDAO.get_by_period_and_status`, `JRIssuesDAO.get_in_keys`.

## Іменування таблиць

`Base.__tablename__` обчислюється через `camel_case_to_snake_case(cls.__name__) + "s"`.
Виняток — `TCEntry`, яка явно задає `__tablename__ = 'tc_entries'` (бо за
дефолтом отримала б `tc_entrys`).

## DTO та валідація

- Кожен зовнішній сервіс має власні Pydantic DTO у `services/<name>/dto.py`
  з `Config.from_attributes = True`.
- ID валідуються через `@field_validator('id', mode='before')` — приводять
  до `int` і повертають `None` для значень `≤ 0`.

## Подієва логіка SQLAlchemy

Два `event.listen`/`@listens_for` хуки:

1. `tc_entry.change_tc_entry_description` — при `set` опису обчислює `task_key`
   через `SyncTaskService.match_task` і кладе у `meta['task']`.
2. `jr_worklog.change_to_description` — при `set` опису worklog парсить шаблон
   `sync|HH:MM|HH:MM - content` і заповнює `meta` (`start_time`, `end_time`,
   `content`).
3. `worklog_sync_task.set_created_at` — `before_insert`/`before_update` ставить
   `created_at`/`updated_at` у `datetime.now(UTC)`.

## SyncTaskService (кеш ключів проектів)

`app/core/utils/sync_task_service.py` тримає **класовий кеш** ключів `JRProject`
і шаблонів `KeyTemplate` із TTL 2 години. `match_task(description)` спершу
шукає шаблон `[A-Z]{2,8}-\d{1,4}` і звіряє префікс зі списком ключів, потім
прокручує regex-шаблони з `KeyTemplate`.

## State machine — `StatusTaskEnum`

```
pre_create → create → created
pre_update → update → updated    (зарезервовано, не використовується)
sync                             (зарезервовано)
```

Перехід `pre_create → create` робить `WorllogSyncTask.before_create`,
перехід `create → created` — `WorllogSyncTask.create_worklogs` після успішного
виклику `Tempo` API.

## State machine — `APIJobStatusEnum`

```
running → needs_verification → verified     (success path)
running → failed                            (exception path)
```

- `running → needs_verification`: `jobs_wrapper.run_job` на normal-exit.
- `running → failed`: `jobs_wrapper.run_job` на exception (потім re-raise).
- `needs_verification → verified`: `POST /api-jobs/{id}/verify` (атомарна
  перевірка в `APIJobDAO.mark_verified`).
- `verified` і `failed` — final-стани. Verify на final → `409 Conflict`,
  verify на `running` → `409 Conflict` ("job has not finished yet").

## Конвенції коду

- Async за замовчуванням; синхронні шляхи (`sync_sessin`, `JRProjectDAO.all_keys_sync`)
  потрібні тільки тому, що `SyncTaskService` викликається з SQLAlchemy
  event-хука, де `await` неможливий.
- `naming_convention` для констрейнтів задається в `DatabaseConfig` і прокидається
  в `Base.metadata`, щоб міграції генерувались зі стабільними іменами.

## Каркас дані-екранів (frontend)

Усі дані-/табличні екрани (`front/src/views/`) будуються на **єдиному каркасі**
`components/data/DataPage.vue` (зміна `add-page-shell-template`) — не копіпастять
`.page`-обгортку руками. `DataPage` дає: заголовок (`title`+опц.`desc`), дії у
верхньому правому куті (слот `#actions`), **закладки** (окремі під-сторінки —
props `tabs`/`activeTab` + подія `update:activeTab`; **router-agnostic**:
навігацію робить в'юха, як `ProjectsView`), опційний суб-бар (слот `#toolbar` —
`pipe`/chips/фільтри), авто-банер помилки (prop `error`) і тіло (default-слот у
`.page__body`). Порядок: заголовок → закладки → тулбар → банер → тіло. CSS —
наявні класи `.page*`/`.data-error` (`styles/shell.css`). **Новий табличний
екран = `DataPage` + вміст.** Виняток — `CalendarView` (власний `.cal`-grid, не
таблиця).

## Єдина «мова синку» (frontend) — обовʼязковий патерн

Стан синку (синхронізовано / не синхронізовано) — **суть продукту**, тож його
відображення і фільтр MUST виглядати **ідентично** на всіх дані-екранах. Для цього
є **два спільні компоненти** (`rework-timecamp-entries-screen`, D11):

- `components/data/SyncState.vue` — індикатор рядка: крапка + короткий підпис
  (`Synced` / `Not synced`). Клас `.syncst` (`.is-on` = зелений).
- `components/data/SyncFilter.vue` — сегментований фільтр `All | Synced |
  Not synced` поверх `Segmented`; оперує канонічним tri-станом
  `SyncTri = 'all' | 'synced' | 'unsynced'` (`api/types.ts`).

Підписи — **англійською в обох локалях** (свідомо: єдиний короткий словник синку;
захардкоджено в компонентах, без i18n-дивергенції). Семантика «synced» залежить від
екрана (worklog у Tempo для записів `/timecamp`; `is_sync` для TimeCamp-проектів;
`is_watched` для Jira-проектів), але **вигляд — один**. Застосовано на `/timecamp`,
`/projects/timecamp`, `/projects/jira`; стори зводять `tcActive`/`jrActive`/
`tcSyncFilter` до `SyncTri`.

**Правило:** будь-який **новий дані-екран зі станом синку MUST переюзовувати**
`SyncState`/`SyncFilter`, а не вводити власний стиль/підписи. Дата в таблицях —
український формат `дд.мм.рррр` через `lib/format.ts → fmtDate`.

## Деталізовані описи інтеграцій

- [TimeCamp](../technical/integrations/timecamp.md) — клієнт, DTO, моделі, DAO,
  парсинг `description`, повний DDL таблиць `tc_projects`, `tc_entries`,
  `key_templates`.
- [Jira + Tempo](../technical/integrations/jira.md) — `JiraService` (4
  endpoint-и для `api/2` + `tempo-timesheets/4`), DTO, моделі `jr_*`,
  каскадне `JRIssuesDAO.sync_by_key`, `UpdateJiraTask`, state-machine
  `WorllogSyncTask` (pre_create → create → created), парсинг
  `sync|HH:MM|HH:MM - content` у `JRWorklog.meta`.
