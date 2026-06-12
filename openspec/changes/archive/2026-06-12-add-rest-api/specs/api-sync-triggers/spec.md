## ADDED Requirements

### Requirement: Every sync trigger records an `api_jobs` row

Будь-який виклик `POST /sync/**` SHALL створити рядок у `api_jobs` із
`status = running`, `trigger_name = <ім'я endpoint-а>`, `payload = <request
body або query>`, `created_by = <username з JWT>`, `started_at = now()`.
Після успіху SHALL виконати `UPDATE status = needs_verification, result =
<counts>, finished_at = now()`. На виключенні SHALL виконати
`UPDATE status = failed, error = <текст>, finished_at = now()`. Деталі
лайфсайклу — capability `api-jobs`.

#### Scenario: Job row created on trigger

- **WHEN** клієнт `POST /sync/timecamp/projects` із валідним токеном
- **THEN** у `api_jobs` з'являється новий рядок із `status = running` ДО початку виконання task

#### Scenario: Job transitions to needs_verification on success

- **GIVEN** task `TimeCampUpdateTask.update_project()` завершується без виключень
- **WHEN** виконання `POST /sync/timecamp/projects` повертає `200 OK`
- **THEN** рядок `api_jobs` для цього виклику має `status = needs_verification`, `finished_at IS NOT NULL`,
  `result IS NOT NULL`

#### Scenario: Job transitions to failed on exception

- **GIVEN** task піднімає виключення посеред виконання
- **WHEN** виконання `POST /sync/timecamp/projects` поглинає виключення
- **THEN** рядок `api_jobs` має `status = failed`, `error IS NOT NULL`, `finished_at IS NOT NULL`; HTTP-відповідь —
  `500 Internal Server Error` із `{job_id: <uuid>, detail: <text>}`

### Requirement: Sync responses contain `job_id` and current `status`

Усі `POST /sync/**` SHALL повертати у body поле `job_id: <uuid>` і
`status: "needs_verification" | "running"`. Поле `result` присутнє у
відповіді тільки коли `status = needs_verification`.

#### Scenario: Synchronous response shape

- **WHEN** клієнт `POST /sync/timecamp/projects` (без `?background`)
- **THEN** відповідь `200 OK` із
  `{job_id: <uuid>, status: "needs_verification", result: {created, updated, deleted, total}}`

#### Scenario: Background response shape

- **WHEN** клієнт `POST /sync/timecamp/projects?background=true`
- **THEN** відповідь `202 Accepted` із `{job_id: <uuid>, status: "running"}`; результат отримується пізніше через
  `GET /api-jobs/{id}`

### Requirement: TimeCamp project sync trigger

Система SHALL надавати `POST /sync/timecamp/projects` без body. Endpoint
виконує `TimeCampUpdateTask.update_project()` у обгортці `api_jobs`-lifecycle.

#### Scenario: Successful project sync

- **WHEN** клієнт `POST /sync/timecamp/projects` із валідним токеном
- **THEN** запускається `TimeCampUpdateTask.update_project()`; після завершення відповідь `200 OK` із
  `{job_id, status: "needs_verification", result: {created, updated, deleted, total}}`

### Requirement: TimeCamp entries sync trigger with period

Система SHALL надавати `POST /sync/timecamp/entries` із body `{start: <ISO
date>, end: <ISO date>}`. Виконує `TimeCampUpdateTask.update_entries(start,
end)` у обгортці `api_jobs`-lifecycle і повертає `result` із лічильниками.

#### Scenario: Successful entries sync

- **WHEN** клієнт `POST /sync/timecamp/entries` із валідним body
- **THEN** відповідь `200 OK` із `{job_id, status: "needs_verification", result: {created, updated, deleted, total}}`
  для
  таблиці `tc_entries` у вказаному періоді

#### Scenario: Missing period

- **WHEN** body не містить `start` або `end`
- **THEN** відповідь `422 Unprocessable Entity` із FastAPI-валідаційним detail; `api_jobs`-рядок НЕ створюється (
  валідація
  виконується до wrapper-а)

### Requirement: Jira project sync trigger

Система SHALL надавати `POST /sync/jira/projects` без body. Endpoint
викликає `UpdateJiraTask.update_all_projects()` у обгортці `api_jobs`.

#### Scenario: Successful sync

- **WHEN** клієнт `POST /sync/jira/projects`
- **THEN** відповідь `200 OK` із `{job_id, status: "needs_verification", result: {created, updated, total}}`

### Requirement: Jira issues sync trigger by keys

Система SHALL надавати `POST /sync/jira/issues` із body `{keys: [<string>]}`.
Endpoint викликає `UpdateJiraTask.update_jira_issues(keys)` у обгортці
`api_jobs`.

#### Scenario: Sync by explicit key list

- **WHEN** клієнт `POST /sync/jira/issues` із `{keys: ["LDI-12", "PEG-7"]}`
- **THEN** відповідь `200 OK` із `{job_id, status: "needs_verification", result: {requested: 2, created, updated}}`; під
  капотом виконується
  `JiraService.search_issues` + каскадний `JRIssuesDAO.sync_by_key`

#### Scenario: Empty keys array

- **WHEN** клієнт `POST /sync/jira/issues` із `{keys: []}`
- **THEN** відповідь `400 Bad Request` із `{detail: "keys must be non-empty"}` (без виклику Jira); `api_jobs`-рядок НЕ
  створюється

### Requirement: Jira worklog sync trigger with period

Система SHALL надавати `POST /sync/jira/worklogs` із body `{start, end}`.
Endpoint викликає `UpdateJiraTask.update_worklog(start, end)` із `worker =
<worker_key з JWT>`. Якщо `worker_key IS NULL` у токені — `400 Bad Request`
до створення api_jobs-рядка.

#### Scenario: Successful worklog import

- **WHEN** клієнт `POST /sync/jira/worklogs` із валідним body і токеном, що має `worker_key`
- **THEN** відповідь `200 OK` із `{job_id, status: "needs_verification", result: {worklogs_synced, issues_refreshed}}`.
  `issues_refreshed` — кількість унікальних issue_key, що додатково оновились після імпорту worklog-ів.

#### Scenario: Missing worker_key in token

- **GIVEN** JWT містить `worker_key = null`
- **WHEN** клієнт `POST /sync/jira/worklogs`
- **THEN** відповідь `400 Bad Request` із `{detail: "user has no worker_key configured"}`; api_jobs НЕ створюється

### Requirement: Worklog sync tasks — prepare stage

Система SHALL надавати `POST /sync/worklog-tasks/prepare` із body `{start,
end}`. Виконує `WorllogSyncTask.create_task_for_sync(start, end)` у обгортці
`api_jobs`.

#### Scenario: Successful prepare

- **WHEN** клієнт `POST /sync/worklog-tasks/prepare`
- **THEN** відповідь `200 OK` із `{job_id, status: "needs_verification", result: {created}}` — кількість нових
  `worklog_sync_tasks` зі статусом `pre_create`

### Requirement: Worklog sync tasks — resolve issues stage

Система SHALL надавати `POST /sync/worklog-tasks/resolve-issues` із body
`{start, end}`. Виконує `WorllogSyncTask.before_create(start, end)` у
обгортці `api_jobs`.

#### Scenario: Successful resolve

- **WHEN** клієнт `POST /sync/worklog-tasks/resolve-issues`
- **THEN** відповідь `200 OK` із `{job_id, status: "needs_verification", result: {resolved, fetched_from_jira}}`.
  `fetched_from_jira` — кількість відсутніх раніше issue_key, які було підтягнуто через
  `UpdateJiraTask.update_jira_issues`.

### Requirement: Worklog sync tasks — push to Tempo stage

Система SHALL надавати `POST /sync/worklog-tasks/push-to-tempo` із body
`{start, end}`. Виконує `WorllogSyncTask.create_worklogs(start, end)` із
worker_key з JWT, у обгортці `api_jobs`. Аналогічно `Jira worklog sync` —
`worker_key IS NULL` дає `400`.

#### Scenario: Successful push

- **WHEN** клієнт `POST /sync/worklog-tasks/push-to-tempo` із токеном з `worker_key`
- **THEN** відповідь `200 OK` із `{job_id, status: "needs_verification", result: {pushed, failed}}`. Кожен успішний
  POST у Tempo переводить task у `created` і пише `target_id`.

#### Scenario: Tempo failure mid-batch

- **GIVEN** Tempo API повертає помилку для одного з worklog-ів
- **WHEN** клієнт `POST /sync/worklog-tasks/push-to-tempo`
- **THEN** успішно створені worklog-и зберігаються (`status = created`), невдалі лишаються у `create`; відповідь
  `200 OK` із `{job_id, status: "needs_verification", result: {pushed: <ok>, failed: <error>}}`. **Endpoint не падає на
  проміжний exception** — батч ідемпотентний для повторного запуску. `api_jobs.status = needs_verification` (НЕ failed),
  оскільки часткове виконання — це нормальний випадок.

### Requirement: All sync triggers require auth

Усі sync-endpoint-и (`/sync/**`) SHALL вимагати валідний Bearer токен (див. `api-auth`).

#### Scenario: Anonymous access denied

- **WHEN** клієнт викликає будь-який `/sync/**` endpoint без `Authorization`
- **THEN** відповідь `401 Unauthorized`
