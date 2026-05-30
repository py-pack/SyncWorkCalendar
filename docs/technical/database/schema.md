# Database Schema — db_swc

Ground-truth довідник по схемі локальної Postgres БД `db_swc`. Усі таблиці,
колонки, типи, ключі, індекси та enum-и зафіксовані з **живої БД** через
PyCharm DataGrip MCP станом на 2026-05-13. Поточний `alembic head`:
`ef2c7288bbb0` (додано `api_users` + `api_jobs` для HTTP-шару).

Якщо схема змінилась — оновити цей файл одним прогоном (див. §9). Усі деталі
поведінки (як саме поле читається/пишеться) — у інтеграційних доках і
`../../memory-bank/systemPatterns.md`. Тут — лише форма даних.

> Візуальний компаньйон — [erd.md](erd.md): ER-діаграма усіх таблиць, flow
> потоку даних і state-machine у Mermaid.

## 1. Загальні конвенції

- **Один schema:** `public`. Інших схем у `db_swc` нема.
- **Іменування таблиць:** `snake_case(ClassName) + "s"` (виняток —
  `TCEntry → tc_entries`).
- **Імена констрейнтів** генеруються `naming_convention` із
  `DatabaseConfig` (`src/config.py`): `pk_<table>`, `uq_<table>_<col>`,
  `ix_<table>_<col>`. Звідси стабільні автогенеровані migration-и.
- **FK constraints не оголошені ніде.** Усі зв'язки між таблицями тримаються
  логікою застосунку (SQLAlchemy `relationship(..., primaryjoin=...,
  foreign(...))`). При DELETE батьківського запису діти не каскадуються —
  з'являються висячі id (див. §7).
- **id PK** усюди — `integer` з `nextval('<table>_id_seq')`. Унікальні
  доменні ключі (`tc_projects.name`, `jr_projects.key`, `jr_users.key`,
  `jr_issues.key`) винесені окремими UNIQUE-індексами.
- **Часові поля:**
  - `created_at` / `updated_at` — `timestamp with time zone` (TIMESTAMPTZ),
    дефолт `now()`.
  - **Виняток:** `tc_entries.start_at` / `end_at` — `timestamp` **без**
    timezone (приходять з TimeCamp як локальний час, див. §7).

---

## 2. TimeCamp-домен

Деталі семантики й API-маппінга — `../integrations/timecamp.md`.

### `tc_projects`

Проекти/задачі з TimeCamp. PK — це `id` з TimeCamp (НЕ surrogate).

| column        | type        | NN | default                              | примітка                                        |
| ------------- | ----------- | -- | ------------------------------------ | ----------------------------------------------- |
| `id`          | integer     | ✓  | `nextval('tc_projects_id_seq')`      | PK — реальний `task_id` із TimeCamp             |
| `name`        | varchar     | ✓  | —                                    | UNIQUE; ім'я задачі (унікальне в акаунті TC)    |
| `parent_id`   | integer     |    | —                                    | ієрархія TimeCamp                               |
| `user_id`     | integer     |    | —                                    | TimeCamp `assigned_by`                          |
| `level`       | smallint    | ✓  | `1`                                  | глибина в ієрархії TC                           |
| `is_archived` | boolean     | ✓  | `false`                              | прийшло з TimeCamp                              |
| `is_sync`     | boolean     | ✓  | `false`                              | **локальний прапор** — entries проекту синкаються в worklog тільки коли `true` |
| `issue_key`   | varchar     |    | —                                    | fallback Jira key, коли в опису entry ключ не знайдено |
| `color`       | varchar     |    | —                                    | колір з TimeCamp                                |
| `created_at`  | timestamptz |    | `now()`                              |                                                 |
| `updated_at`  | timestamptz |    | `now()`                              |                                                 |

**Keys / indices:** `pk_tc_projects(id)`, `uq_tc_projects_name(name)`.

### `tc_entries`

Таймер-записи з TimeCamp. PK — реальний entry id з TimeCamp.

| column          | type        | NN | default                                       | примітка                                                       |
| --------------- | ----------- | -- | --------------------------------------------- | -------------------------------------------------------------- |
| `id`            | integer     | ✓  | `nextval('tc_entries_id_seq')`                | PK                                                             |
| `tc_project_id` | integer     |    | —                                             | м'який зв'язок → `tc_projects.id` (без FK)                     |
| `description`   | varchar     |    | —                                             | event-listener `'set'` парсить → `meta['task']` (див. §6)      |
| `meta`          | json        |    | —                                             | `{"task": "<JIRA-KEY>"}` або `null`                            |
| `start_at`      | timestamp   | ✓  | —                                             | **без timezone** — як приходить з TC                           |
| `end_at`        | timestamp   | ✓  | —                                             | **без timezone**                                               |
| `duration`      | integer     | ✓  | `EXTRACT(epoch FROM (end_at - start_at))`     | **GENERATED STORED**, не записується з коду                    |
| `updated_at`    | timestamptz |    | `now()`                                       |                                                                |

**Keys / indices:** `pk_tc_entries(id)`. Більше індексів нема — пошук по
періоду йде по `start_at` через seq scan (для поточних обсягів ОК).

---

## 3. Jira-домен

Дані, що віддзеркалюються з Jira on-prem (`leadsdoit.io/jira/...`).

### `jr_projects`

| column        | type    | NN | default                          | примітка                                                  |
| ------------- | ------- | -- | -------------------------------- | --------------------------------------------------------- |
| `id`          | integer | ✓  | `nextval('jr_projects_id_seq')`  | PK (surrogate — Jira id не реюзаємо)                      |
| `key`         | varchar | ✓  | —                                | UNIQUE; project key з Jira (`LDI`, `LSP`, ...)           |
| `name`        | varchar | ✓  | —                                |                                                           |
| `is_archved`  | boolean | ✓  | —                                | ⚠️ **typo в назві** (має бути `is_archived`) — див. §8     |
| `is_watched`  | boolean | ✓  | —                                | локальний прапор, чи цей проект тягнеться в синк          |

**Keys / indices:** `pk_jr_projects(id)`, `uq_jr_projects_key(key)`.

### `jr_users`

| column      | type    | NN | default                       | примітка                                  |
| ----------- | ------- | -- | ----------------------------- | ----------------------------------------- |
| `id`        | integer | ✓  | `nextval('jr_users_id_seq')`  | PK                                        |
| `key`       | varchar | ✓  | —                             | UNIQUE; Jira username/account-key         |
| `name`      | varchar |    | —                             | display name                              |
| `full_name` | varchar |    | —                             |                                           |
| `email`     | varchar |    | —                             |                                           |

**Keys / indices:** `pk_jr_users(id)`, `uq_jr_users_key(key)`.

### `jr_issues`

| column             | type        | NN | default                        | примітка                                          |
| ------------------ | ----------- | -- | ------------------------------ | ------------------------------------------------- |
| `id`               | integer     | ✓  | `nextval('jr_issues_id_seq')`  | PK (surrogate)                                    |
| `key`              | varchar     | ✓  | —                              | UNIQUE; Jira issue key (`LDI-123`)                |
| `name`             | varchar     | ✓  | —                              | summary                                           |
| `jr_project_id`    | integer     | ✓  | —                              | м'який FK → `jr_projects.id`, indexed             |
| `epic_key`         | varchar     |    | —                              | indexed; ключ Epic-а, не FK                       |
| `parent_key`       | varchar     |    | —                              | indexed; ключ батьківської задачі                 |
| `type`             | varchar     | ✓  | —                              | issue type (`Task`, `Bug`, ...)                   |
| `priority`         | varchar     | ✓  | —                              |                                                   |
| `status`           | varchar     | ✓  | —                              |                                                   |
| `jr_creator_key`   | varchar     |    | —                              | indexed; → `jr_users.key`                         |
| `jr_reporter_key`  | varchar     |    | —                              | indexed; → `jr_users.key`                         |
| `estimate_plan`    | integer     | ✓  | `0`                            | секунди; `timeoriginalestimate`                   |
| `estimate_fact`    | integer     | ✓  | `0`                            | секунди; `aggregateprogress.progress`             |
| `estimate_rest`    | integer     | ✓  | `0`                            | секунди; `aggregatetimeestimate`                  |
| `created_at`       | timestamptz |    | `now()`                        |                                                   |
| `updated_at`       | timestamptz |    | `now()`                        |                                                   |

**Keys / indices:** `pk_jr_issues(id)`, `uq_jr_issues_key(key)`,
`ix_jr_issues_jr_project_id`, `ix_jr_issues_epic_key`,
`ix_jr_issues_parent_key`, `ix_jr_issues_jr_creator_key`,
`ix_jr_issues_jr_reporter_key`.

### `jr_worklogs`

Worklog-и з Jira (через Tempo). Не плутати з `worklog_sync_tasks` —
ця таблиця тільки **читає** з Tempo та зберігає поточний стан.

| column           | type        | NN | default                          | примітка                                                   |
| ---------------- | ----------- | -- | -------------------------------- | ---------------------------------------------------------- |
| `id`             | integer     | ✓  | `nextval('jr_worklogs_id_seq')`  | PK — реальний worklog id з Tempo                           |
| `jr_issues_id`   | integer     | ✓  | —                                | ⚠️ ім'я `jr_issues_id` (з `s`) — див. §8. Indexed; → `jr_issues.id` |
| `description`    | varchar     | ✓  | —                                | сирий текст worklog-а; event-listener `'set'` парсить `sync\|HH:MM\|HH:MM - <content>` у `meta` |
| `meta`           | json        |    | —                                | `{start_time, end_time, content}` або `{content}`         |
| `jr_worker_key`  | varchar     |    | —                                | indexed; → `jr_users.key`                                  |
| `started_at`     | timestamptz | ✓  | —                                | момент початку worklog-а (з Tempo)                         |
| `duration`       | integer     | ✓  | `0`                              | секунди витраченого часу                                   |
| `created_at`     | timestamptz |    | `now()`                          |                                                            |
| `updated_at`     | timestamptz |    | `now()`                          |                                                            |

**Keys / indices:** `pk_jr_worklogs(id)`, `ix_jr_worklogs_jr_issues_id`,
`ix_jr_worklogs_jr_worker_key`. **Унікальність на `(jr_issues_id, started_at,
jr_worker_key)` НЕ заведена** — теоретично можливі дублі при повторних
імпортах. Захист — `BaseDAO.sync_all` робить full-replace за `id`.

---

## 4. Sync-домен

### `worklog_sync_tasks`

Черга/журнал задач синхронізації `TimeCamp entry → Tempo worklog`.
State-machine — у `../../memory-bank/systemPatterns.md`.

| column        | type                              | NN | default                                | примітка                                                 |
| ------------- | --------------------------------- | -- | -------------------------------------- | -------------------------------------------------------- |
| `id`          | integer                           | ✓  | `nextval('worklog_sync_tasks_id_seq')` | PK (surrogate)                                           |
| `status`      | `worklog_sync_status_task_enum`   | ✓  | —                                      | див. §5 enum-значення                                    |
| `source_id`   | integer                           | ✓  | —                                      | indexed; → `tc_entries.id`                               |
| `target_id`   | integer                           |    | —                                      | indexed; → `jr_worklogs.id` після створення в Tempo      |
| `worker_key`  | varchar                           | ✓  | —                                      | → `jr_users.key`                                         |
| `issue_key`   | varchar                           | ✓  | —                                      | Jira issue key, у який створюється worklog               |
| `issue_id`    | integer                           |    | —                                      | indexed; → `jr_issues.id` (опційно)                      |
| `content`     | varchar                           |    | —                                      | текст для Tempo (`sync\|HH:MM\|HH:MM - <desc>`)          |
| `started_at`  | timestamptz                       | ✓  | —                                      | від якого моменту worklog                                |
| `time_spent`  | integer                           | ✓  | —                                      | секунди                                                  |
| `created_at`  | timestamptz                       |    | `now()` (також ставиться before_insert)| хук `set_created_at`                                     |
| `updated_at`  | timestamptz                       |    | `now()` (також ставиться before_update)| хук `set_created_at`                                     |

**Keys / indices:** `pk_worklog_sync_tasks(id)`,
`ix_worklog_sync_tasks_source_id`, `ix_worklog_sync_tasks_target_id`,
`ix_worklog_sync_tasks_issue_id`.

### `key_templates`

Шаблони для парсингу опису `tc_entry.description → Jira issue_key`.
Семантика — `../integrations/timecamp.md` §7.

| column      | type    | NN | default                            | примітка                                            |
| ----------- | ------- | -- | ---------------------------------- | --------------------------------------------------- |
| `id`        | integer | ✓  | `nextval('key_templates_id_seq')`  | PK                                                  |
| `issue_key` | varchar | ✓  | —                                  | цільовий Jira issue_key                             |
| `template`  | varchar | ✓  | —                                  | `/regex/` або escaped substring (case-insensitive) |

**Keys / indices:** `pk_key_templates(id)`. UNIQUE на `template` НЕ заведено —
теоретично можливі дублі.

---

## 5. Системні таблиці

### `alembic_version`

| column        | type        | NN | default | примітка                              |
| ------------- | ----------- | -- | ------- | ------------------------------------- |
| `version_num` | varchar(32) | ✓  | —       | PK; поточне значення: `ef2c7288bbb0`  |

---

## 5a. API-домен

Таблиці HTTP-шару (capability `api-auth` + `api-jobs`). Жодних FK на доменні
таблиці (`tc_*`, `jr_*`) — звʼязок `api_users.worker_key ↔ Jira key` тримається
застосунком (див. §8).

### `api_users`

Користувачі HTTP API. Заведення — **ручний INSERT** (інструкція в
`docs/technical/api-reference.md` § «Перший користувач»); CLI для керування —
окрема майбутня зміна `add-user-management-cli`. Schема навмисно multi-user-ready,
див. `decisinLog.md` → D-009.

| column          | type        | NN | default                            | примітка                                            |
| --------------- | ----------- | -- | ---------------------------------- | --------------------------------------------------- |
| `id`            | integer     | ✓  | `nextval('api_users_id_seq')`      | PK                                                  |
| `username`      | varchar     | ✓  | —                                  | UNIQUE (`uq_api_users_username`); імʼя для login    |
| `password_hash` | varchar     | ✓  | —                                  | bcrypt-хеш                                          |
| `worker_key`    | varchar     |    | —                                  | Jira key для sync-trigger-ів; null → 400 на worklog-енд |
| `is_active`     | boolean     | ✓  | —                                  | `false` → login завжди повертає 401                 |
| `created_at`    | timestamptz | ✓  | —                                  | ставиться event-листенером `_stamp_api_user_timestamps` |
| `updated_at`    | timestamptz | ✓  | —                                  | оновлюється тим же листенером перед UPDATE          |

### `api_jobs`

Журнал sync-операцій. Кожен `POST /sync/**` створює рядок зі `status=running`,
потім перехід у `needs_verification` (після успіху) або `failed`. Ручний
`POST /api-jobs/{id}/verify` переводить у `verified`. Деталі lifecycle — у
`docs/technical/api-reference.md` і `decisinLog.md` → D-010.

| column         | type                   | NN | default                | примітка                                            |
| -------------- | ---------------------- | -- | ---------------------- | --------------------------------------------------- |
| `id`           | uuid                   | ✓  | `gen_random_uuid()`    | PK; UUID, бо джерело id — додаток, не sequence      |
| `trigger_name` | varchar                | ✓  | —                      | напр. `sync.timecamp.entries`; INDEX                |
| `status`       | `api_job_status_enum`  | ✓  | —                      | див. §6; INDEX                                      |
| `payload`      | jsonb                  |    | —                      | request body або query                              |
| `result`       | jsonb                  |    | —                      | counts після успіху                                 |
| `error`        | text                   |    | —                      | str(exception) при `failed`                         |
| `created_by`   | varchar                | ✓  | —                      | `api_users.username` (без FK)                       |
| `verified_by`  | varchar                |    | —                      | `api_users.username` верифікатора                   |
| `started_at`   | timestamptz            | ✓  | —                      | INDEX; час входу в endpoint                         |
| `finished_at`  | timestamptz            |    | —                      | заповнюється при переході зі `running`              |
| `verified_at`  | timestamptz            |    | —                      | заповнюється лише при `verified`                    |

CHECK-constraints:

- `ck_api_jobs_verified_at_only_when_verified`: `verified_at IS NULL OR status = 'verified'`
- `ck_api_jobs_finished_at_only_when_not_running`: `finished_at IS NULL OR status <> 'running'`

---

## 6. Enum-типи

### `api_job_status_enum`

Доменний enum для `api_jobs.status` (`src/models/api_job.py` →
`APIJobStatusEnum`):

```
running  →  needs_verification  →  verified    ← основний потік
running  →  failed                              ← на виключенні
```

Переходи (`src/api/jobs_wrapper.py`):

- `running → needs_verification` — на нормальний вихід wrapper-а.
- `running → failed` — на exception, перед re-raise.
- `needs_verification → verified` — `POST /api-jobs/{id}/verify`.

`verified` і `failed` — final-стани, з них немає виходу.

### `worklog_sync_status_task_enum`

Доменний enum для `worklog_sync_tasks.status`. Значення приходять з
`StatusTaskEnum` (`src/models/worklog_sync_task.py`):

```
pre_create  →  create  →  created       ← основний потік
pre_update  →  update  →  updated       ← зарезервовано, не використовується
sync                                    ← зарезервовано
```

Переходи:
- `pre_create → create` — `WorllogSyncTask.before_create`.
- `create → created` — `WorllogSyncTask.create_worklogs` після успіху Tempo API.

---

## 7. Sequences

Один sequence на кожну `id`-колонку, генеровано Alembic:

```
jr_issues_id_seq, jr_projects_id_seq, jr_users_id_seq,
jr_worklogs_id_seq, key_templates_id_seq, tc_entries_id_seq,
tc_projects_id_seq, worklog_sync_tasks_id_seq,
api_users_id_seq
```

`api_jobs.id` — UUID, без sequence (PK генерується `gen_random_uuid()` на стороні Postgres).

Для `tc_projects` / `tc_entries` / `jr_worklogs` sequence-и фактично **не
використовуються** при імпорті — id приходять із зовнішнього API. Sequence
залишається на випадок ручних INSERT-ів і не синхронізується з реальними
імпортованими значеннями — теоретично `nextval()` може повернути id, що вже
зайнятий зовнішнім імпортом.

---

## 8. Soft links (без FK constraint)

Жоден FK не оголошено. Логічні зв'язки:

- `api_jobs.created_by → api_users.username` — пишеться з JWT-claim. UNIQUE
  гарантує однозначність, але видалення юзера лишить «висячі» рядки `api_jobs`.
- `api_jobs.verified_by → api_users.username` — те саме.
- `api_users.worker_key` — це Jira key користувача (напр. `alice`). У JWT-claim
  кладеться той же worker_key і використовується як параметр sync-тригерів
  worklog-domain-у (`/sync/jira/worklogs`, `/sync/worklog-tasks/push-to-tempo`).
  Звʼязок із Jira — поза цією БД.

Інші логічні зв'язки доменних таблиць:

```
tc_entries.tc_project_id        →  tc_projects.id
tc_projects.issue_key           →  jr_issues.key                        (fallback)
jr_issues.jr_project_id         →  jr_projects.id
jr_issues.epic_key              →  jr_issues.key                        (self, по полю key)
jr_issues.parent_key            →  jr_issues.key                        (self, по полю key)
jr_issues.jr_creator_key        →  jr_users.key
jr_issues.jr_reporter_key       →  jr_users.key
jr_worklogs.jr_issues_id        →  jr_issues.id
jr_worklogs.jr_worker_key       →  jr_users.key
worklog_sync_tasks.source_id    →  tc_entries.id
worklog_sync_tasks.target_id    →  jr_worklogs.id                       (після створення)
worklog_sync_tasks.issue_id     →  jr_issues.id                         (опц.)
worklog_sync_tasks.worker_key   →  jr_users.key
worklog_sync_tasks.issue_key    →  jr_issues.key
key_templates.issue_key         →  jr_issues.key
tc_entries.meta['task']         →  jr_issues.key                        (через парсер)
jr_worklogs.meta.start_time     →  HH:MM, парситься з description
```

Наслідок: цілісність забезпечує тільки код (`BaseDAO.sync_all`,
event-listeners, ручні селекти). Будь-яке прямі `DELETE` через `psql`
залишає висячі id в дочірніх таблицях.

---

## 9. Quirks / тех-борги

- **`jr_projects.is_archved`** — typo в назві колонки (має бути
  `is_archived`). Зафіксовано в моделі та міграції; перейменовувати потрібно
  парою «модель + alembic-ревізія». Не міняти руками в БД.
- **`jr_worklogs.jr_issues_id`** — ім'я з зайвою `s`. Решта таблиць використовує
  однину (`tc_project_id`, `jr_project_id`). Виправлення тягне за собою
  оновлення моделі, DAO, alembic ревізії та існуючих даних.
- **`WorllogSyncTask`** (typo в назві класу/модуля) — це **код**, не БД, але
  про нього варто пам'ятати: таблиця в БД називається коректно
  (`worklog_sync_tasks`), а Python-клас і файл — `WorllogSyncTask`. Перейменування
  обережне.
- **`tc_entries.start_at` / `end_at`** — без timezone. Порівняння з
  `worklog_sync_tasks.started_at` (TIMESTAMPTZ) дає неявний каст.
- **`tc_entries.duration`** — `GENERATED STORED`. Не можна передавати з коду
  (SQLAlchemy `Computed`). При зміні `start_at`/`end_at` перераховується
  автоматично.
- **`worklog_sync_status_task_enum`** містить значення (`pre_update`,
  `update`, `updated`, `sync`), які поточний потік **не використовує**. Можуть
  бути плановими розширеннями state-machine.
- **Жодних FK** — при потребі цілісності використовувати `BaseDAO.sync_all`
  / `sync_all_between`, а не ручні DELETE.
- **Sequence-и для імпортованих id** (`tc_*`, `jr_worklogs`) рано чи пізно
  можуть колізіювати з зовнішніми id. Поки що сценаріїв ручних INSERT-ів
  немає.

---

## 10. Як оновити цей файл

Документ — снапшот живої БД, отриманий через PyCharm DataGrip MCP. Щоб
перевірити дрейф або оновити після нової міграції:

1. `alembic current` — порівняти з рядком у §5.
2. Скіл `db-introspection` (`.claude/skills/db-introspection/SKILL.md`,
   дзеркало `.agents/skills/db-introspection/SKILL.md`) містить готові
   виклики `mcp__pycharm__get_database_object_description` для кожної
   таблиці. Прогнати по всім — отриманий DDL порівняти з §2-5.
3. Якщо БД не піднята — `docker compose up -d db` + `alembic upgrade head`.
4. Оновити цей файл + (за потреби) рядок з `alembic head` у вступі.
5. Якщо змінилась структура (нова колонка, новий зв'язок, новий enum) —
   синхронно оновити `erd.md` (ER-діаграма, flow, state-machine).

Не правити вміст руками без звірки з MCP — це ground-truth, не пам'ять.
