# api-sync-status Specification

## Purpose

Read-only status endpoints that expose sync metadata: TC/Jira projects with
their flags and counts, worklog sync task aggregations, and untracked TC
entries. Period-based endpoints share consistent validation.
## Requirements
### Requirement: List TC projects with sync metadata

Система SHALL надавати `GET /tc-projects` з опційними query-параметрами
`?start=<ISO date>&end=<ISO date>` (дефолт — поточний місяць у UTC).
Відповідь SHALL містити список усіх записів `tc_projects` + лічильник
`tc_entries` за вказаний період.

#### Scenario: Default period returns all projects

- **WHEN** клієнт `GET /tc-projects` без параметрів
- **THEN** відповідь `200 OK` із масивом `[{id, name, is_sync, issue_key, is_archived, entries_count}]`, де
  `entries_count` — кількість `tc_entries.start_at` у `[поч. місяця, кін. місяця]`

#### Scenario: Custom period filters entries count

- **WHEN** клієнт `GET /tc-projects?start=2026-04-01&end=2026-04-30`
- **THEN** `entries_count` у кожному елементі рахується за період `2026-04-01 00:00 .. 2026-04-30 23:59` по
  `tc_entries.start_at`

#### Scenario: Invalid date format

- **WHEN** клієнт передає `start=not-a-date`
- **THEN** відповідь `422 Unprocessable Entity` із FastAPI-валідаційним detail

### Requirement: List Jira projects with sync metadata

Система SHALL надавати `GET /jr-projects`. Відповідь SHALL містити список `jr_projects` із поточними прапорами та
кількістю пов'язаних `jr_issues`.

#### Scenario: Default response

- **WHEN** клієнт `GET /jr-projects`
- **THEN** відповідь `200 OK` із масивом `[{id, key, name, is_archived, is_watched, issues_count}]`, де `issues_count` —
  `COUNT(*) FROM jr_issues WHERE jr_project_id = <id>`

### Requirement: Worklog sync tasks status overview

Система SHALL надавати `GET /worklog-sync-tasks` з обовʼязковим періодом-фільтром,
опційним `?status=<StatusTaskEnum>`, опційним фільтром стану синку `?synced = all |
synced | unsynced` (`synced` = `target_id IS NOT NULL`), пошуком `?q=` (за **назвою**
задачі) і серверною пагінацією (`limit` дефолт 50/кап ≤200, `offset`). Відповідь SHALL
містити агрегацію по статусах (`summary`, по всьому періоду — не лише по сторінці),
`total` і перелік задач сторінки; кожен елемент SHALL містити `issue_name` (резолв
через `jr_issues`, може бути `null`).

#### Scenario: Aggregation per status

- **WHEN** клієнт `GET /worklog-sync-tasks?start=2026-04-01&end=2026-04-30`
- **THEN** відповідь `200 OK` із тілом `{summary: {pre_create: <int>, create: <int>,
  created: <int>, ...}, total: <int>, items: [<WorklogSyncTaskDTO з issue_name>]}`, де
  `summary` рахує `worklog_sync_tasks.status` за `started_at` у періоді

#### Scenario: Filter by single status

- **WHEN** клієнт додає `&status=create`
- **THEN** `items` містить лише задачі зі `status = create`; `summary` залишається
  повним по всіх статусах періоду

#### Scenario: Фільтр стану синку і пошук

- **WHEN** клієнт додає `&synced=unsynced&q=<частина назви>`
- **THEN** `items` містить лише ще не запушені (`target_id IS NULL`) задачі, чия задача
  має назву, що містить `q`; пагінація застосовується, `total` відображає відфільтровану
  кількість

#### Scenario: Empty period

- **WHEN** період не має жодного `worklog_sync_tasks` запису
- **THEN** відповідь `200 OK` із `{summary: {<all enum keys>: 0}, total: 0, items: []}`

### Requirement: Untracked TC entries lookup

Система SHALL надавати `GET /tc-entries/untracked` із обов'язковим періодом. Відповідь — entries без `meta.task` і без
матчу через `tc_projects.issue_key` батьківського проекту, тобто ті, що не зможуть створити worklog без ручного
втручання.

#### Scenario: Entry without meta and project issue_key

- **GIVEN** `tc_entries.meta IS NULL` і `tc_projects.issue_key IS NULL` для батьківського `tc_project_id`
- **WHEN** клієнт `GET /tc-entries/untracked?start=2026-04-01&end=2026-04-30`
- **THEN** entry присутній у відповіді з полями `{id, description, start_at, end_at, tc_project_id, tc_project_name}`

#### Scenario: Entry resolved via project fallback

- **GIVEN** `tc_entries.meta IS NULL`, але `tc_projects.issue_key = 'LDI-42'`
- **WHEN** клієнт `GET /tc-entries/untracked` за той самий період
- **THEN** entry **не** включається у відповідь (fallback покриє його при синку)

#### Scenario: Entry has meta task

- **GIVEN** `tc_entries.meta = {"task": "LDI-7"}`
- **WHEN** клієнт `GET /tc-entries/untracked`
- **THEN** entry **не** включається у відповідь

### Requirement: Period validation across status endpoints

Усі status-endpoint-и із параметром періоду SHALL відмовляти при `start > end` з `400 Bad Request` і
`detail: "start must be <= end"`.

#### Scenario: Inverted period

- **WHEN** клієнт `GET /worklog-sync-tasks?start=2026-04-30&end=2026-04-01`
- **THEN** відповідь `400 Bad Request` із `{detail: "start must be <= end"}`

### Requirement: TimeCamp entries list with sync state and pagination

Система SHALL надавати `GET /tc-entries`, що повертає записи TimeCamp
(`tc_entries`) за період із локальної БД, із похідним станом синхронізації,
фільтром стану та серверною пагінацією. Цей ендпоінт **не** ховає зіставлені
записи (на відміну від `GET /tc-entries/untracked`).

Параметри запиту:

- `start`, `end` (date) — період за `tc_entries.start_at`. Якщо не задані —
  дефолт **поточний місяць** (перше … останнє число).
- `synced` — `all | synced | unsynced` (дефолт `all`).
- `limit` (дефолт `50`, максимум `200`), `offset` (дефолт `0`).

Відповідь — обʼєкт `{ items, total }`, де кожен `item` містить
`{ id, description, start_at, end_at, tc_project_id, tc_project_name, issue_key,
is_synced }`:

- `issue_key` — резолв `tc_entries.meta.task`, інакше `issue_key` батьківського
  `tc_project` (може бути `null`).
- `is_synced` — `true`, якщо для запису існує `worklog_sync_task` зі статусом
  `created` або `updated`, приєднаний за `source_id = tc_entries.id` **і**
  `worker_key = <worker_key поточного користувача>`; інакше `false`.
- `total` — кількість записів за тим самим фільтром (період + `synced`), без
  урахування `limit`/`offset`.

Записи MUST сортуватися за `start_at` спадно.

#### Scenario: Default period and pagination

- **WHEN** клієнт `GET /tc-entries` без параметрів
- **THEN** повертаються записи за поточний місяць, відсортовані за `start_at`
  спадно, не більше `50` у `items`, із повним `total` за період

#### Scenario: Filter only synced entries

- **GIVEN** запис має `worklog_sync_task` зі статусом `created` для `worker_key`
  поточного користувача
- **WHEN** клієнт `GET /tc-entries?synced=synced`
- **THEN** цей запис присутній у `items` із `is_synced = true`, а записи без
  worklog у Tempo не включаються

#### Scenario: Filter only unsynced entries

- **GIVEN** запис не має `worklog_sync_task` у статусі `created`/`updated` для
  `worker_key` поточного користувача
- **WHEN** клієнт `GET /tc-entries?synced=unsynced`
- **THEN** цей запис присутній у `items` із `is_synced = false`

#### Scenario: Sync state scoped by worker_key

- **GIVEN** запис має `worklog_sync_task` у статусі `created`, але з **іншим**
  `worker_key`
- **WHEN** клієнт `GET /tc-entries?synced=all`
- **THEN** запис має `is_synced = false` (чужий стан синку не протікає)

#### Scenario: Pagination total is independent of limit/offset

- **WHEN** клієнт `GET /tc-entries?limit=10&offset=20`
- **THEN** `items` містить не більше `10` записів, починаючи зі зміщення `20`, а
  `total` дорівнює повній кількості записів за фільтром

#### Scenario: issue_key resolved from meta then project

- **GIVEN** запис має `meta = {"task": "LDI-7"}`
- **WHEN** клієнт `GET /tc-entries`
- **THEN** `item.issue_key = "LDI-7"`
- **GIVEN** запис має `meta IS NULL`, а батьківський `tc_project.issue_key = "LDI-42"`
- **THEN** `item.issue_key = "LDI-42"`

#### Scenario: Period validation

- **WHEN** клієнт `GET /tc-entries?start=2026-05-31&end=2026-05-01`
- **THEN** відповідь `400 Bad Request` із `detail` про `start must be <= end`

### Requirement: Список Tempo-worklog-ів з БД (`GET /jr-worklogs`)

Система SHALL надавати `GET /jr-worklogs`, що повертає реальні Tempo-worklog-и з
локальної БД (`jr_worklogs`) поточного користувача (scoped по `worker_key` із JWT)
за період, із серверною пагінацією. Параметри: `start`/`end` (дата; дефолт —
поточний місяць), `linked = all | linked | unlinked` (дефолт `all`), `q` (пошук за
**назвою** задачі, `ILIKE`), `limit` (дефолт 50, кап ≤200), `offset`. Відповідь —
`{ items, total }`, де кожен елемент містить похідне `is_linked` (через **EXISTS** на
`worklog_sync_tasks.target_id = jr_worklogs.id`) і `issue_name` (резолв через
`jr_issues`, може бути `null`). Endpoint MUST вимагати валідний Bearer-токен.

#### Scenario: Читання Tempo-worklog-ів за період

- **WHEN** авторизований клієнт `GET /jr-worklogs?start=…&end=…`
- **THEN** відповідь `200 OK` із `{ items, total }` — worklog-и користувача в періоді,
  кожен із похідним `is_linked` та `issue_name`

#### Scenario: Фільтр звʼязку

- **WHEN** клієнт `GET /jr-worklogs?linked=unlinked`
- **THEN** повертаються лише worklog-и без WST-містка (`is_linked = false`)

#### Scenario: Пошук за назвою задачі

- **WHEN** клієнт `GET /jr-worklogs?q=<частина назви>`
- **THEN** повертаються лише worklog-и, чия задача має назву, що містить `q`

#### Scenario: Без токена

- **WHEN** клієнт `GET /jr-worklogs` без `Authorization`
- **THEN** відповідь `401 Unauthorized`

