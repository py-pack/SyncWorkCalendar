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

Поле `status` у кожному елементі відповіді MUST серіалізуватися як **рядкове
значення** enum (одне з `running`/`needs_verification`/`verified`/`failed`), а
не як Python enum-обʼєкт. Серіалізація відповіді MUST бути коректною за
наявності будь-якої кількості рядків у `api_jobs` (регрес-гард).

Відповідь MUST додатково містити `summary` — кількість job-ів по кожному
статусу (`running`/`needs_verification`/`verified`/`failed`), пораховану за
фільтром **періоду+тригера** (`start`/`end`/`trigger_name`), **ігноруючи** фільтр
`status` (щоб зведення показувало повну картину вибірки). Шейп відповіді:
`{items: [<APIJobSummary>], total: <int>, summary: {running, needs_verification, verified, failed}}`.

#### Scenario: List with status filter

- **WHEN** клієнт `GET /api-jobs?status=needs_verification`
- **THEN** відповідь `200 OK`; `items` — тільки рядки зі `status = needs_verification`,
  відсортовано за `started_at DESC`; `total` — їх кількість

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
- **THEN** відповідь `200 OK`, і кожен елемент має `status` як рядок — **не** `500`

#### Scenario: Summary рахується за періодом, не за статус-фільтром

- **GIVEN** у періоді є job-и різних статусів
- **WHEN** клієнт `GET /api-jobs?status=verified&start=...&end=...`
- **THEN** `items` містять лише `verified`, але `summary` показує кількості **всіх**
  чотирьох статусів за тим самим періодом+тригером

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

### Requirement: Bulk verify endpoint

Система SHALL надавати `POST /api-jobs/verify-all` із query-фільтрами
`?start=<ISO date>&end=<ISO date>` (опційно, за `started_at`) і
`?trigger_name=<string>` (опційно). Ендпоінт MUST одним атомарним `UPDATE`
перевести **всі** job-и зі `status = needs_verification`, що підпадають під
фільтри, у `status = verified` (`verified_at = now()`,
`verified_by = <username з JWT>`), і повернути `{verified: <int>}` — кількість
підтверджених. Ендпоінт MUST зачіпати лише `needs_verification` (state machine:
`running`/`verified`/`failed` не змінюються). Маршрут вимагає авторизації.

#### Scenario: Підтвердити всі за фільтром

- **GIVEN** у періоді є 40 job-ів `needs_verification` і кілька `verified`/`failed`
- **WHEN** користувач (username = "alice") `POST /api-jobs/verify-all?start=...&end=...`
- **THEN** відповідь `200 OK` із `{verified: 40}`; усі 40 стали `verified`
  (`verified_by = "alice"`, `verified_at = now()`); `verified`/`failed`/`running`
  не зачеплені

#### Scenario: Нічого підтверджувати

- **WHEN** під фільтр не підпадає жоден `needs_verification`
- **THEN** відповідь `200 OK` із `{verified: 0}`; жодного рядка не змінено

#### Scenario: Анонімний доступ заборонено

- **WHEN** клієнт `POST /api-jobs/verify-all` без `Authorization`
- **THEN** відповідь `401 Unauthorized`

### Requirement: Automatic job retention (auto-verify + TTL deletion)

Система SHALL за розкладом прибирати `api_jobs` так, щоб журнал не зростав
безмежно:

- **Авто-verify за віком:** job-и зі `status = needs_verification` і
  `finished_at < now() - N днів` MUST автоматично переходити у `status = verified`
  (`verified_at = now()`, `verified_by = "system"`), де `N` —
  `APP__CELERY__AUTO_VERIFY_DAYS` (дефолт `7`). Перехід MUST зачіпати лише
  `needs_verification` (поважає state machine); `running`/`failed` не чіпаються.
- **TTL-видалення:** job-и зі `status IN (verified, failed)` і
  `finished_at < now() - M днів` MUST видалятися, де `M` —
  `APP__CELERY__JOB_TTL_DAYS` (дефолт `90`). `running` і `needs_verification`
  **ніколи** не видаляються.

#### Scenario: Старий needs_verification авто-verify-иться

- **GIVEN** job `needs_verification` із `finished_at` 10 днів тому, `N = 7`
- **WHEN** відпрацьовує планове прибирання
- **THEN** job стає `verified` із `verified_by = "system"`, `verified_at = now()`

#### Scenario: Свіжий needs_verification лишається

- **GIVEN** job `needs_verification` із `finished_at` 2 дні тому, `N = 7`
- **WHEN** відпрацьовує планове прибирання
- **THEN** job лишається `needs_verification` (не молодші за TTL не чіпаються)

#### Scenario: Старий термінальний видаляється

- **GIVEN** job `verified` (або `failed`) із `finished_at` 100 днів тому, `M = 90`
- **WHEN** відпрацьовує планове прибирання
- **THEN** рядок видаляється з `api_jobs`

#### Scenario: running ніколи не видаляється і не verify-иться авто

- **GIVEN** job `running` (як завгодно старий)
- **WHEN** відпрацьовує планове прибирання
- **THEN** рядок лишається незмінним

### Requirement: Retry failed job endpoint

Система SHALL надавати `POST /api-jobs/{job_id}/retry` (вимагає авторизації), що
**синхронно** повторює одну впавшу job-у:

- Job-а MUST існувати (інакше `404`) і мати `status = failed` (інакше `409` —
  ретраяться лише впалі; `running`/`needs_verification`/`verified` не повторюються).
- Ендпоінт MUST взяти `trigger_name` і збережений `payload` впалої job-и та
  прогнати **ту саму** роботу через спільний реєстр `trigger_name → робота`, який
  перевикористовує наявні sync-обробники (один і той самий код, що й у відповідного
  sync-тригера). Якщо `trigger_name` невідомий реєстру — `422` (`"trigger is not
  retryable"`).
- Ретрай MUST створити **нову** `api_jobs`-джобу (`created_by` = користувач із JWT)
  і прогнати її через життєвий цикл `running → needs_verification` (успіх) або
  `running → failed` (виняток). Стара впала job-а MUST лишитись незмінною в історії.
- Відповідь MUST бути `200 OK` із `APIJobDetail` **нової** job-и — у **обох**
  випадках (успіх і повторне падіння); синхронна невдача роботи MUST NOT давати
  `500` (нова job-а просто матиме `status = failed` зі своїм `error`).

#### Scenario: Перезапуск впалої job-и — успіх

- **GIVEN** job-а `J1` зі `status = failed`, `trigger_name = sync.worklog-tasks.push-to-tempo`
  і збереженим `payload`
- **WHEN** користувач `POST /api-jobs/{J1}/retry`
- **THEN** створюється **нова** job-а `J2` із тим самим `trigger_name`/`payload`,
  прогнана синхронно; відповідь `200 OK` з `APIJobDetail` `J2`
  (`status = needs_verification`); `J1` лишається `failed`

#### Scenario: Перезапуск знову падає

- **GIVEN** впала job-а, чия причина ще не усунена
- **WHEN** користувач `POST /api-jobs/{id}/retry`
- **THEN** нова job-а стає `failed` зі своїм `error`; відповідь `200 OK` з
  `APIJobDetail` нової (впалої) job-и — **не** `500`

#### Scenario: Ретрай не-failed job-и заборонено

- **GIVEN** job-а зі `status = needs_verification` (або `verified`/`running`)
- **WHEN** користувач `POST /api-jobs/{id}/retry`
- **THEN** відповідь `409 Conflict`; жодної нової job-и не створено

#### Scenario: Невідомий тригер не ретраїться

- **GIVEN** впала job-а, чий `trigger_name` відсутній у реєстрі ретраю
- **WHEN** користувач `POST /api-jobs/{id}/retry`
- **THEN** відповідь `422`; жодної нової job-и не створено

#### Scenario: Неіснуюча job-а

- **WHEN** користувач `POST /api-jobs/{невідомий_id}/retry`
- **THEN** відповідь `404 Not Found`

#### Scenario: Анонімний доступ заборонено

- **WHEN** клієнт `POST /api-jobs/{id}/retry` без `Authorization`
- **THEN** відповідь `401 Unauthorized`

