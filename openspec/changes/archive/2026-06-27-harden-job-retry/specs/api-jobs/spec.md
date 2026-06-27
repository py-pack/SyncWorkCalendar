## MODIFIED Requirements

### Requirement: Status transitions follow strict state machine

Система MUST дозволяти лише такі переходи `api_jobs.status`:
`running → needs_verification`, `running → failed`,
`needs_verification → verified`, **`failed → running`** (рестарт через ретрай,
лише атомарним compare-and-swap — див. вимогу «Retry failed job endpoint»).
Будь-який інший перехід SHALL бути відхилений на рівні DAO/моделі. `verified` —
final-стан, з нього немає виходу. `failed` — final-стан **за винятком** єдиного
переходу `failed → running` через ретрай.

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

#### Scenario: Retry transitions failed to running

- **GIVEN** `api_jobs.status = failed`
- **WHEN** користувач викликає `POST /api-jobs/{id}/retry` і compare-and-swap успішний
- **THEN** `UPDATE api_jobs SET status = running, started_at = now(), finished_at = NULL,
  error = NULL, result = NULL` для **того самого** рядка

#### Scenario: Verify on terminal status rejected

- **GIVEN** `api_jobs.status IN ('failed', 'verified')`
- **WHEN** користувач `POST /api-jobs/{id}/verify`
- **THEN** відповідь `409 Conflict` із `{detail: "job is already in terminal status: <status>"}`

#### Scenario: Verify on running rejected

- **GIVEN** `api_jobs.status = running` (background-task ще виконується)
- **WHEN** користувач `POST /api-jobs/{id}/verify`
- **THEN** відповідь `409 Conflict` із `{detail: "job has not finished yet"}`

### Requirement: Retry failed job endpoint

Система SHALL надавати `POST /api-jobs/{job_id}/retry` (вимагає авторизації), що
**синхронно перезапускає ту саму** впавшу job-у **на місці** (без створення нової
`api_jobs`-джоби):

- Job-а MUST існувати (інакше `404`).
- Рестарт MUST виконуватися через **атомарний compare-and-swap**
  `failed → running`: одним `UPDATE ... WHERE id = :id AND status = 'failed'` рядок
  переводиться у `running` (`started_at = now()`, `finished_at = NULL`,
  `error = NULL`, `result = NULL`). Якщо CAS не зачепив жодного рядка (job-а **не**
  `failed` — уже `running` від попереднього кліку, або `needs_verification`/
  `verified`) — відповідь `409 Conflict` (`"job is not in failed status"`), і
  **жодна** робота не запускається. CAS — самодостатній guard від подвійного
  запуску: одночасно стартує лише **один** ретрай.
- Після успішного CAS ендпоінт MUST взяти `trigger_name` і збережений `payload` цієї
  job-и та прогнати **ту саму** роботу через спільний реєстр `trigger_name → робота`,
  який перевикористовує наявні sync-обробники. Якщо `trigger_name` невідомий реєстру —
  job-а MUST бути закрита у `failed` із поясненням, а відповідь — `422` (`"trigger is
  not retryable"`); guard уже зайняв рядок, тож CAS все одно лишається коректним.
- Той самий рядок MUST бути закритий за наслідком роботи: `running →
  needs_verification` (успіх) або `running → failed` (виняток), кожне у власній
  короткій сесії (як `jobs_wrapper`).
- Відповідь MUST бути `200 OK` із `APIJobDetail` **того самого** рядка (`id` не
  змінюється) — у **обох** випадках (успіх і повторне падіння); синхронна невдача
  роботи MUST NOT давати `500`.

#### Scenario: Перезапуск впалої job-и на місці — успіх

- **GIVEN** job-а `J1` зі `status = failed`, `trigger_name = sync.worklog-tasks.push-to-tempo`
  і збереженим `payload`
- **WHEN** користувач `POST /api-jobs/{J1}/retry`
- **THEN** `J1` атомарно переходить `failed → running`, прогоняється синхронно і
  закривається у `needs_verification`; відповідь `200 OK` з `APIJobDetail` **того
  самого** `J1` (`status = needs_verification`); **нового** рядка не створено

#### Scenario: Повторний/паралельний клік під час running відхиляється

- **GIVEN** ретрай job-и `J1` уже захопив рядок (`status = running`)
- **WHEN** надходить другий `POST /api-jobs/{J1}/retry`
- **THEN** compare-and-swap не зачіпає рядок; відповідь `409 Conflict`; **жодна**
  додаткова робота не запускається (дубль не створюється)

#### Scenario: Перезапуск знову падає

- **GIVEN** впала job-а, чия причина ще не усунена
- **WHEN** користувач `POST /api-jobs/{id}/retry`
- **THEN** **той самий** рядок стає `failed` зі своїм новим `error`; відповідь
  `200 OK` з `APIJobDetail` цього рядка — **не** `500`

#### Scenario: Ретрай не-failed job-и заборонено

- **GIVEN** job-а зі `status = needs_verification` (або `verified`/`running`)
- **WHEN** користувач `POST /api-jobs/{id}/retry`
- **THEN** відповідь `409 Conflict`; статус рядка не змінюється; жодної роботи не запущено

#### Scenario: Неіснуюча job-а

- **WHEN** користувач `POST /api-jobs/{невідомий_id}/retry`
- **THEN** відповідь `404 Not Found`

#### Scenario: Анонімний доступ заборонено

- **WHEN** клієнт `POST /api-jobs/{id}/retry` без `Authorization`
- **THEN** відповідь `401 Unauthorized`
