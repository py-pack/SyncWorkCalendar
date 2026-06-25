## MODIFIED Requirements

### Requirement: List jobs endpoint with filters

Система SHALL надавати `GET /api-jobs` із query-параметрами:
`?status=<api_job_status_enum>` (опційно), `?trigger_name=<string>`
(опційно), `?start=<ISO date>&end=<ISO date>` (опційно, фільтр по
`started_at`), `?limit=<int>&offset=<int>` (дефолт 50/0, max 500).

Поле `status` у кожному елементі відповіді MUST серіалізуватися як **рядкове
значення** enum (одне з `running`/`needs_verification`/`verified`/`failed`), а
не як Python enum-обʼєкт. Серіалізація відповіді MUST бути коректною за
наявності будь-якої кількості рядків у `api_jobs` (регрес-гард: раніше
`model_validate(<ORM>)` кидав `ValidationError`, бо `Literal[str]` не приймав
enum-member, і ендпоінт повертав `500`).

#### Scenario: List with status filter

- **WHEN** клієнт `GET /api-jobs?status=needs_verification`
- **THEN** відповідь `200 OK` із `{items: [<APIJobSummary>], total: <int>}` — тільки рядки зі
  `status = needs_verification`, відсортовано за `started_at DESC`

#### Scenario: List default response

- **WHEN** клієнт `GET /api-jobs` без параметрів
- **THEN** відповідь `200 OK` із 50 останніх рядків (DESC by `started_at`)

#### Scenario: Combined filters

- **WHEN** клієнт `GET /api-jobs?status=failed&trigger_name=sync.jira.worklogs&start=2026-05-01&end=2026-05-11`
- **THEN** фільтр AND по всіх трьох: `status = failed` AND `trigger_name = '...'` AND
  `started_at BETWEEN '2026-05-01' AND '2026-05-11 23:59'`

#### Scenario: Non-empty table serializes without error

- **GIVEN** у `api_jobs` є щонайменше один рядок (будь-якого статусу)
- **WHEN** клієнт `GET /api-jobs` (із фільтром чи без)
- **THEN** відповідь `200 OK`, і кожен елемент має `status` як рядок
  (`running`/`needs_verification`/`verified`/`failed`) — **не** `500`

### Requirement: Get single job detail

Система SHALL надавати `GET /api-jobs/{id}`, що повертає повний рядок
`api_jobs` із усіма колонками (включно з `payload`, `result`, `error`). Поле
`status` MUST серіалізуватися як рядкове значення enum (як у списку).

#### Scenario: Existing job

- **WHEN** клієнт `GET /api-jobs/<valid-uuid>`
- **THEN** відповідь `200 OK` із
  `{id, trigger_name, status, payload, result, error, created_by, verified_by, started_at, finished_at, verified_at}`,
  де `status` — рядок

#### Scenario: Non-existing job

- **WHEN** клієнт `GET /api-jobs/<random-uuid>`
- **THEN** відповідь `404 Not Found` із `{detail: "api job not found"}`

#### Scenario: Invalid UUID

- **WHEN** клієнт `GET /api-jobs/not-a-uuid`
- **THEN** відповідь `422 Unprocessable Entity` із FastAPI-валідаційним detail
