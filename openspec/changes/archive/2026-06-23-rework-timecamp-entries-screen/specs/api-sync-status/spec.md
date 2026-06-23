## ADDED Requirements

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
