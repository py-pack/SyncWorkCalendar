## ADDED Requirements

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

## MODIFIED Requirements

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
