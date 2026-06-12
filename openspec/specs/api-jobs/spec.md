# api-jobs Specification

## Purpose

Tracks every sync invocation as a row in `api_jobs`, enforces a strict status
state machine over the job lifecycle, and exposes endpoints to list, inspect,
and verify jobs. All routes require authentication.

## Requirements

### Requirement: `api_jobs` table tracks every sync invocation

Система SHALL зберігати в таблиці `api_jobs` рядок про кожен виклик
`POST /sync/**`, який пройшов авторизацію і request-валідацію. Колонки:
`id (UUID PK)`, `trigger_name`, `status (api_job_status_enum)`, `payload
(JSONB)`, `result (JSONB)`, `error (TEXT)`, `created_by`, `verified_by`,
`started_at`, `finished_at`, `verified_at`.

#### Scenario: Row created on trigger entry

- **WHEN** будь-який `POST /sync/**` проходить authn + request-валідацію
- **THEN** у `api_jobs` з'являється рядок: `status = running`, `started_at = now()`, `payload = <body|query>`,
  `created_by = <username з JWT>`, `trigger_name = <ім'я endpoint-а, напр. "sync.timecamp.entries">`

#### Scenario: Row not created on validation error

- **GIVEN** request не проходить Pydantic-валідацію (наприклад, `start > end`, порожні `keys`, неавтентифікований запит)
- **WHEN** клієнт викликає sync-endpoint
- **THEN** жодного рядка `api_jobs` не створюється; HTTP-відповідь `400/401/422` як визначено у capability
  `api-sync-triggers`

### Requirement: Status transitions follow strict state machine

Система MUST дозволяти лише такі переходи `api_jobs.status`:
`running → needs_verification`, `running → failed`,
`needs_verification → verified`. Будь-який інший перехід SHALL бути
відхилений на рівні DAO/моделі. `verified` і `failed` — final-стани, з них
немає виходу.

#### Scenario: Successful completion transitions to needs_verification

- **GIVEN** `api_jobs.status = running`
- **WHEN** task завершується без виключень
- **THEN** `UPDATE api_jobs SET status = needs_verification, finished_at = now(), result = <counts>`

#### Scenario: Exception transitions to failed

- **GIVEN** `api_jobs.status = running`
- **WHEN** task піднімає виключення
- **THEN** `UPDATE api_jobs SET status = failed, finished_at = now(), error = <stringified exception>`

#### Scenario: Verify transitions to verified

- **GIVEN** `api_jobs.status = needs_verification`
- **WHEN** користувач викликає `POST /api-jobs/{id}/verify`
- **THEN** `UPDATE api_jobs SET status = verified, verified_at = now(), verified_by = <username з JWT>`

#### Scenario: Verify on terminal status rejected

- **GIVEN** `api_jobs.status IN ('failed', 'verified')`
- **WHEN** користувач `POST /api-jobs/{id}/verify`
- **THEN** відповідь `409 Conflict` із `{detail: "job is already in terminal status: <status>"}`

#### Scenario: Verify on running rejected

- **GIVEN** `api_jobs.status = running` (background-task ще виконується)
- **WHEN** користувач `POST /api-jobs/{id}/verify`
- **THEN** відповідь `409 Conflict` із `{detail: "job has not finished yet"}`

### Requirement: List jobs endpoint with filters

Система SHALL надавати `GET /api-jobs` із query-параметрами:
`?status=<api_job_status_enum>` (опційно), `?trigger_name=<string>`
(опційно), `?start=<ISO date>&end=<ISO date>` (опційно, фільтр по
`started_at`), `?limit=<int>&offset=<int>` (дефолт 50/0, max 500).

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

### Requirement: Get single job detail

Система SHALL надавати `GET /api-jobs/{id}`, що повертає повний рядок
`api_jobs` із усіма колонками (включно з `payload`, `result`, `error`).

#### Scenario: Existing job

- **WHEN** клієнт `GET /api-jobs/<valid-uuid>`
- **THEN** відповідь `200 OK` із
  `{id, trigger_name, status, payload, result, error, created_by, verified_by, started_at, finished_at, verified_at}`

#### Scenario: Non-existing job

- **WHEN** клієнт `GET /api-jobs/<random-uuid>`
- **THEN** відповідь `404 Not Found` із `{detail: "api job not found"}`

#### Scenario: Invalid UUID

- **WHEN** клієнт `GET /api-jobs/not-a-uuid`
- **THEN** відповідь `422 Unprocessable Entity` із FastAPI-валідаційним detail

### Requirement: Verify job endpoint

Система SHALL надавати `POST /api-jobs/{id}/verify` без body. Endpoint
переводить job із `needs_verification` у `verified` (див. state machine).

#### Scenario: Successful verify

- **GIVEN** `api_jobs.status = needs_verification`
- **WHEN** клієнт `POST /api-jobs/{id}/verify` із валідним токеном (username = "alice")
- **THEN** відповідь `200 OK` із оновленим `APIJob` (status = verified, verified_at = now(), verified_by = "alice")

### Requirement: All api-jobs routes require auth

Система SHALL вимагати валідний Bearer токен (див. `api-auth`) для всіх
endpoint-ів `GET /api-jobs`, `GET /api-jobs/{id}` і
`POST /api-jobs/{id}/verify`.

#### Scenario: Anonymous access denied

- **WHEN** клієнт викликає будь-який `/api-jobs/**` без `Authorization`
- **THEN** відповідь `401 Unauthorized`
