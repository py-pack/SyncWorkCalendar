## ADDED Requirements

### Requirement: Пуш одного worklog-task за id

Система SHALL надавати `POST /sync/worklog-tasks/{id}/push`, що пушить у Tempo
**один** `WorklogSyncTask` за його `id` (через наявну `create_worklogs`-логіку,
обмежену цим записом), у обгортці `api_jobs`-lifecycle. Якщо `worker_key IS NULL` у
токені — `400 Bad Request` до створення `api_jobs`-рядка; якщо запис не знайдено —
`404 Not Found`. Дедуп проти `jr_worklogs` (capability `backend-auto-linking`) MUST
застосовуватись і тут.

#### Scenario: Успішний пуш одного рядка

- **WHEN** авторизований клієнт із `worker_key` викликає `POST
  /sync/worklog-tasks/{id}/push` для запису у статусі `create`/`created`
- **THEN** виконується створення/звірка Tempo-worklog-а саме для цього запису,
  відповідь `200 OK` із `{job_id, status: "needs_verification", result}`, статус
  переходить у `created`

#### Scenario: Запис не знайдено

- **WHEN** клієнт викликає `POST /sync/worklog-tasks/{id}/push` з неіснуючим `id`
- **THEN** відповідь `404 Not Found`; `api_jobs`-рядок не створюється

#### Scenario: Немає worker_key

- **GIVEN** JWT містить `worker_key = null`
- **WHEN** клієнт викликає `POST /sync/worklog-tasks/{id}/push`
- **THEN** відповідь `400 Bad Request`; `api_jobs`-рядок не створюється
