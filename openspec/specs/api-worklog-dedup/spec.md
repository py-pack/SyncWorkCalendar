# api-worklog-dedup Specification

## Purpose
TBD - created by archiving change add-worklog-dedup-cleanup. Update Purpose after archive.
## Requirements
### Requirement: Перелік груп дубльованих worklog-ів

Система SHALL надавати `GET /jr-worklogs/duplicates` (вимагає авторизації), що
повертає групи **дубльованих** Tempo-worklog-ів поточного `worker_key`. Дублем
вважаються ≥2 рядки `jr_worklogs` із однаковим ключем
`(jr_issues_id, jr_worker_key, started_at, duration)` — **тим самим**, що
використовує `JRWorklogDAO.find_match` для дедупу перед пушем. Endpoint MUST:

- бути scoped по `worker_key` із JWT (чужі worklog-и не повертаються); без
  `worker_key` у токені — порожній результат;
- приймати опційний період `?start=<ISO date>&end=<ISO date>` за `started_at`
  (дефолт — поточний місяць); `start` MUST бути `<= end`, інакше `400`;
- групувати за ключем дедупу й лишати лише групи з `count > 1`;
- повертати для кожної групи: поля ключа (`jr_issues_id`, `started_at`,
  `duration`), `issue_key`/`issue_name` (join `jr_issues`), `count`, і перелік
  членів (`id`, `description`, `created_at`, `is_linked` — чи вказує на нього
  якийсь `WST.target_id`).

#### Scenario: Знайдено дублі за період

- **GIVEN** у періоді є три `jr_worklogs` з однаковим `(issue, worker, started_at,
  duration)` і кілька унікальних
- **WHEN** авторизований клієнт `GET /jr-worklogs/duplicates?start=...&end=...`
- **THEN** відповідь `200 OK`; повертається одна група з `count = 3` і трьома
  членами; унікальні worklog-и (`count = 1`) не повертаються

#### Scenario: Дублів немає

- **WHEN** клієнт `GET /jr-worklogs/duplicates` за період без дублів
- **THEN** відповідь `200 OK` з порожнім списком груп

#### Scenario: Валідація періоду

- **WHEN** клієнт `GET /jr-worklogs/duplicates?start=2026-05-31&end=2026-05-01`
- **THEN** відповідь `400 Bad Request` (`start must be <= end`)

#### Scenario: Без токена

- **WHEN** клієнт `GET /jr-worklogs/duplicates` без `Authorization`
- **THEN** відповідь `401 Unauthorized`

### Requirement: Масова чистка дублів worklog-ів

Система SHALL надавати `POST /jr-worklogs/dedup` (вимагає авторизації), що
**реально видаляє** зайві worklog-и обраних груп із Tempo. Endpoint MUST:

- вимагати `worker_key` у JWT — без нього `400` (`"user has no worker_key
  configured"`), бо видалення в Tempo персональне;
- приймати в тілі перелік груп для чистки (за ключем дедупу або переліком
  `worklog_id`); чистка діє **лише** на передані групи, а не на всі дублі;
- у кожній групі **лишати один** worklog — той, на який вказує наявний
  `WorklogSyncTask.target_id`; якщо такого немає або їх кілька — лишати worklog із
  найменшим `id`;
- для **кожного** worklog-а на видалення: викликати **новий**
  `JiraService.delete_worklog` (`DELETE tempo-timesheets/4/worklogs/{id}`); після
  успішного Tempo-видалення — видалити рядок `jr_worklogs` і **перенацілити** будь-
  який `WST.target_id`, що вказував на видалений worklog, на залишений (звʼязок не
  розривається);
- бути ідемпотентно-безпечним до помилок: помилка видалення одного worklog-а MUST
  NOT валити всю дію — рядок збирається в `errors`, локальне дзеркало для нього NOT
  видаляється, чистка триває далі;
- осідати в `api_jobs` як аудит (через `run_job`, `trigger_name =
  "worklog.dedup-cleanup"`);
- повертати підсумок `{deleted, kept, groups, errors: [{worklog_id, reason}]}`.

#### Scenario: Чистка обраної групи

- **GIVEN** група з трьох однакових worklog-ів, один із яких має `WST.target_id`
- **WHEN** користувач `POST /jr-worklogs/dedup` із цією групою
- **THEN** worklog із `WST` лишається; два інші видаляються з Tempo
  (`delete_worklog`) і з `jr_worklogs`; відповідь містить `{deleted: 2, kept: 1,
  groups: 1, errors: []}`

#### Scenario: Перелінк WST на залишений worklog

- **GIVEN** група, де `WST.target_id` вказує на worklog, який потрапив під
  видалення (а лишається інший)
- **WHEN** виконується чистка
- **THEN** `WST.target_id` перенацілюється на залишений worklog (лінк не стає битим)

#### Scenario: Помилка Tempo на одному worklog-у

- **GIVEN** Tempo повертає помилку на видаленні одного з worklog-ів групи
- **WHEN** виконується чистка
- **THEN** цей worklog лишається (потрапляє в `errors`), решта групи прибирається;
  дія не валиться цілком; `api_jobs`-рядок фіксує підсумок

#### Scenario: Без worker_key

- **GIVEN** користувач без `worker_key`
- **WHEN** він `POST /jr-worklogs/dedup`
- **THEN** відповідь `400 Bad Request`; нічого не видаляється

#### Scenario: Без токена

- **WHEN** клієнт `POST /jr-worklogs/dedup` без `Authorization`
- **THEN** відповідь `401 Unauthorized`

### Requirement: Tempo-видалення worklog-у в `JiraService`

`JiraService` SHALL надавати метод `delete_worklog(worklog_id, worker)`, що
видаляє Tempo-worklog через `DELETE tempo-timesheets/4/worklogs/{worklog_id}`.
Метод MUST використовувати `_make_request(..., raise_on_error=True)`, щоб помилка
Tempo (4xx/5xx) **не ковталась**, а піднімалась як `TempoApiError` із тілом
відповіді (узгоджено з фіксом `create_worklog`/`update_worklog`).

#### Scenario: Успішне видалення

- **WHEN** `delete_worklog(originId, worker)` викликано для наявного Tempo-worklog-а
- **THEN** виконується `DELETE tempo-timesheets/4/worklogs/{originId}`; на успіх
  метод повертає керування без помилки

#### Scenario: Помилка Tempo піднімається

- **GIVEN** Tempo відповідає 4xx/5xx на видалення
- **WHEN** викликано `delete_worklog`
- **THEN** піднімається `TempoApiError` із тілом відповіді (помилка не ковтається)

