# System Patterns

## Шари

```
main.py / main.ipynb
   │
   ▼
src/tasks/*                  ← оркестрація (TimeCamp/Jira/Worklog tasks)
   │
   ├─► src/services/*        ← HTTP-клієнти зовнішніх API + DTO (Pydantic)
   │
   └─► src/dao/*             ← робота з БД через SQLAlchemy AsyncSession
            │
            ▼
       src/models/*          ← SQLAlchemy 2.x Declarative моделі
```

- `src/core/db_helper.py` тримає глобальний `async_engine`, `sync_engine`
  і контекст-менеджер `get_async_asession()` (автокоміт на виході, rollback при
  винятку). Клас `DatabaseHelper` лишився як `deprecated`.
- `src/config.py` — `pydantic-settings`, префікс `APP__`, вкладеність через
  `__`. Підвантаження з `.env.template` і `.env`.

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

`src/core/utils/sync_task_service.py` тримає **класовий кеш** ключів `JRProject`
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

## Конвенції коду

- Async за замовчуванням; синхронні шляхи (`sync_sessin`, `JRProjectDAO.all_keys_sync`)
  потрібні тільки тому, що `SyncTaskService` викликається з SQLAlchemy
  event-хука, де `await` неможливий.
- `naming_convention` для констрейнтів задається в `DatabaseConfig` і прокидається
  в `Base.metadata`, щоб міграції генерувались зі стабільними іменами.

## Деталізовані описи інтеграцій

- [TimeCamp](../technical/integrations/timecamp.md) — клієнт, DTO, моделі, DAO,
  парсинг `description`, повний DDL таблиць `tc_projects`, `tc_entries`,
  `key_templates`.
- [Jira + Tempo](../technical/integrations/jira.md) — `JiraService` (4
  endpoint-и для `api/2` + `tempo-timesheets/4`), DTO, моделі `jr_*`,
  каскадне `JRIssuesDAO.sync_by_key`, `UpdateJiraTask`, state-machine
  `WorllogSyncTask` (pre_create → create → created), парсинг
  `sync|HH:MM|HH:MM - content` у `JRWorklog.meta`.
