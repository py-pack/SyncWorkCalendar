## MODIFIED Requirements

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

## ADDED Requirements

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
