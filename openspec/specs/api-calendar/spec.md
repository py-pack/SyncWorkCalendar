# api-calendar Specification

## Purpose

Read-only бекенд тижневого календаря (timesheet): `GET /calendar` повертає
блоки робочого часу авторизованого `worker_key` за період зі станом синку
(`service` / `tempo` / `synced`), зведеним із наявних `tc_entries` ↔
`worklog_sync_tasks` ↔ `tc_projects`. Без нових колонок, міграцій і записів —
запис/sync винесено в майбутні фази.
## Requirements
### Requirement: Читання тижня блоків

Система SHALL надавати `GET /calendar` з параметрами періоду (`start`, `end`
або `week`), що повертає блоки робочого часу авторизованого користувача
(`worker_key` із JWT) за цей період. Endpoint MUST бути **read-only** — він MUST
NOT змінювати дані і MUST NOT вимагати нових колонок у БД (читає наявні
`tc_entries` / `worklog_sync_tasks` / `tc_projects`). Кожен блок MUST містити:
`id`, час (`start`+`end`), проект (`key`/`name`/`color` для кольору),
`issue_key`, опис і **стан синку** (`service` / `tempo` / `synced`). Блоки інших
користувачів MUST NOT повертатися.

#### Scenario: Тиждень поточного користувача

- **WHEN** авторизований клієнт `GET /calendar` із валідним періодом
- **THEN** відповідь `200 OK` зі списком блоків лише для його `worker_key`,
  кожен зі станом синку і даними проекту (колір/назва)

#### Scenario: Період без даних

- **WHEN** клієнт `GET /calendar` за період без записів
- **THEN** відповідь `200 OK` з порожнім списком блоків

### Requirement: Деривація стану синку блоку

Стан блоку SHALL обчислюватися із зв'язку `tc_entries` ↔ `worklog_sync_tasks`:
блок без worklog-таска (або таск у `pre_create`) → `service`; таск у `create`
(готовий до пушу / очікує) → `tempo`; таск `created` із `target_id` у Tempo →
`synced`. Read-шар MUST повертати лише ці три стани. Блок MUST NOT мати стан
`failed` від бекенда — такого статусу у `worklog_sync_tasks`
(`StatusTaskEnum`) немає (`failed` — це стан `api_jobs`, не worklog-таска).

#### Scenario: Несинхронізований блок

- **GIVEN** запис `tc_entry` без `worklog_sync_task` (або таск у `pre_create`)
- **WHEN** клієнт читає тиждень
- **THEN** блок повертається зі станом `service`

#### Scenario: Синхронізований блок

- **GIVEN** блок має `worklog_sync_task.status = created` і `target_id`
- **WHEN** клієнт читає тиждень
- **THEN** блок повертається зі станом `synced`

### Requirement: Доступ до календаря лише за токеном

Усі endpoint-и `/calendar*` MUST вимагати валідний Bearer-токен і працювати
лише з блоками поточного `worker_key`. Без токена → `401`.

#### Scenario: Без токена

- **WHEN** клієнт `GET /calendar` без `Authorization`
- **THEN** відповідь `401 Unauthorized`

### Requirement: Прапор дубля worklog-у на блоці

`GET /calendar` SHALL додавати кожному блоку булевий прапор `duplicate`. Блок MUST
мати `duplicate = true`, якщо в тому ж періоді існує ≥2 рядки `jr_worklogs` з тим
самим ключем дедупу `(jr_issues_id, jr_worker_key, started_at, duration)`, з яким
зіставлений цей блок (через `WorklogSyncTask.target_id` → `jr_worklog` або прямим
матчем за ключем). Прапор обчислюється тим самим групуванням, що
`GET /jr-worklogs/duplicates` (capability `api-worklog-dedup`).

`duplicate` MUST бути **окремим** прапором і MUST NOT впливати на стан синку блоку:
набір станів лишається `service`/`tempo`/`synced` (інваріант «Деривація стану синку
блоку»). Endpoint лишається read-only і не потребує нових колонок у БД.

#### Scenario: Блок із дубльованим worklog-ом

- **GIVEN** worklog блоку має ще один `jr_worklog`-дубль у періоді (той самий ключ)
- **WHEN** авторизований клієнт `GET /calendar`
- **THEN** блок повертається з `duplicate = true`, а його стан синку лишається
  одним із `service`/`tempo`/`synced`

#### Scenario: Звичайний блок без дублів

- **GIVEN** worklog блоку унікальний за ключем дедупу в періоді
- **WHEN** клієнт `GET /calendar`
- **THEN** блок повертається з `duplicate = false`

