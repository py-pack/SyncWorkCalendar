# api-tc-projects-management Specification

## Purpose

Partial update of TimeCamp project sync flags via `PATCH /tc-projects/{id}`.
Only `is_sync` and `issue_key` may be changed, `issue_key` is format-validated,
and the endpoint requires authentication.
## Requirements
### Requirement: Partial update of TC project flags

Система SHALL надавати `PATCH /tc-projects/{id}` із тілом `{is_sync?: bool, issue_key?: string | null}`. Дозволено
оновлювати **лише** ці два поля. Інші поля з body — ігноруються або відхиляються (extra = forbid у Pydantic-схемі —
рекомендовано).

#### Scenario: Toggle is_sync flag

- **GIVEN** `tc_projects.id = 123` існує
- **WHEN** клієнт `PATCH /tc-projects/123` із body `{is_sync: true}`
- **THEN** відповідь `200 OK` із оновленим записом; БД має `tc_projects.is_sync = true` для `id = 123`

#### Scenario: Set issue_key

- **WHEN** клієнт `PATCH /tc-projects/123` із body `{issue_key: "LDI-42"}`
- **THEN** відповідь `200 OK`; БД має `tc_projects.issue_key = 'LDI-42'`

#### Scenario: Clear issue_key

- **WHEN** клієнт `PATCH /tc-projects/123` із body `{issue_key: null}`
- **THEN** відповідь `200 OK`; БД має `tc_projects.issue_key IS NULL`

#### Scenario: Update both fields in one call

- **WHEN** клієнт `PATCH /tc-projects/123` із body `{is_sync: true, issue_key: "LDI-42"}`
- **THEN** відповідь `200 OK`; обидва поля оновлені одним UPDATE-запитом

#### Scenario: Empty body

- **WHEN** клієнт `PATCH /tc-projects/123` із body `{}`
- **THEN** відповідь `400 Bad Request` із `{detail: "body must contain at least one of: is_sync, issue_key"}`

#### Scenario: Non-existing project

- **WHEN** клієнт `PATCH /tc-projects/999999` із валідним body для id, щовідсутній у `tc_projects`
- **THEN** відповідь `404 Not Found` із `{detail: "TC project not found"}`

#### Scenario: Forbidden field in body

- **WHEN** клієнт `PATCH /tc-projects/123` із body `{name: "rename attempt"}`
- **THEN** відповідь `422 Unprocessable Entity` (Pydantic відкидає extra field) **або** ігнорує `name` і повертає
  `400 Bad Request` за правилом «порожнє тіло». Конкретна семантика — на розсуд імплементатора, але `tc_projects.name`
  ніколи не оновлюється через цей endpoint.

### Requirement: Validation of issue_key format

Якщо `issue_key` передається не-null, він SHALL відповідати регулярному виразу `^[A-Z]{2,8}-\d{1,4}$` (формат Jira issue
key). Невалідний формат → `422 Unprocessable Entity`.

#### Scenario: Valid issue_key

- **WHEN** клієнт `PATCH /tc-projects/123` із `{issue_key: "PEG-100"}`
- **THEN** валідація проходить, запис оновлюється

#### Scenario: Invalid issue_key

- **WHEN** клієнт передає `{issue_key: "not-a-key"}`
- **THEN** відповідь `422 Unprocessable Entity` із Pydantic-detail

### Requirement: PATCH requires authentication

Endpoint `PATCH /tc-projects/{id}` SHALL вимагати валідний Bearer токен (див. `api-auth`).

#### Scenario: Anonymous PATCH denied

- **WHEN** клієнт `PATCH /tc-projects/123` без `Authorization`
- **THEN** відповідь `401 Unauthorized`

### Requirement: List TC projects as tree data

Система SHALL надавати `GET /tc-projects`, що повертає **усі** записи
`tc_projects` як плаский список полями, достатніми для побудови дерева й
відображення маппінгу на стороні клієнта. Endpoint MUST вимагати валідний
Bearer-токен (`api-auth`). Кожен елемент відповіді SHALL містити:

- `id` — `int`
- `name` — `str`
- `parent_id` — `int | null` (ID батьківського проекту; корені — `null`)
- `color` — `str | null` (колір проекту з TimeCamp)
- `is_archived` — `bool`
- `is_sync` — `bool`
- `issue_key` — `str | null` (змаплена Jira-задача)
- `issue_name` — `str | null` (назва задачі, резолв через LEFT JOIN
  `jr_issues ON tc_projects.issue_key = jr_issues.key`; `null`, якщо проект не
  змаплено або ключ відсутній у локальних `jr_issues`)
- `issue_active` — `bool | null` (`true`, якщо статус змапованої задачі **не** в
  «done»-сеті; `null`, якщо `issue_name` не резолвнуто)

Endpoint MUST NOT приймати параметри періоду (`start`/`end`) і MUST NOT повертати
per-period лічильник записів — проекти не залежать від дати.

#### Scenario: Повний список з деревними полями

- **WHEN** авторизований клієнт `GET /tc-projects`
- **THEN** відповідь `200 OK` зі списком проектів; кожен елемент містить `id`,
  `name`, `parent_id`, `color`, `is_archived`, `is_sync`, `issue_key`,
  `issue_name`, `issue_active`

#### Scenario: Резолв назви змапованої задачі

- **GIVEN** `tc_projects.issue_key = 'LDI-42'` і в `jr_issues` є `key = 'LDI-42'`
  з `name = 'Fix login'`, статус не завершений
- **WHEN** клієнт `GET /tc-projects`
- **THEN** відповідний елемент має `issue_name = 'Fix login'` і
  `issue_active = true`

#### Scenario: Змаплено на невідому локально задачу

- **GIVEN** `tc_projects.issue_key = 'XXX-9'`, але в `jr_issues` такого ключа нема
- **WHEN** клієнт `GET /tc-projects`
- **THEN** елемент має `issue_key = 'XXX-9'`, `issue_name = null`,
  `issue_active = null`

#### Scenario: Закрита змаплена задача

- **GIVEN** змаплена задача має статус із «done»-сету (напр. `Closed`)
- **WHEN** клієнт `GET /tc-projects`
- **THEN** елемент має `issue_active = false`

#### Scenario: Без параметрів періоду

- **WHEN** клієнт `GET /tc-projects?start=2025-01-01&end=2025-02-01`
- **THEN** параметри `start`/`end` ігноруються (не впливають на вибірку); поля
  `entries_count` у відповіді немає

#### Scenario: Без токена

- **WHEN** клієнт `GET /tc-projects` без `Authorization`
- **THEN** відповідь `401 Unauthorized`

### Requirement: Filter TC projects by archived state

`GET /tc-projects` SHALL підтримувати параметр `active` зі значеннями
`active | inactive | all`, що фільтрує за `tc_projects.is_archived`:
`active` → лише `is_archived = false`; `inactive` → лише `is_archived = true`;
`all` → без фільтра. Значення за замовчуванням — `all`. Невалідне значення →
`422 Unprocessable Entity`.

#### Scenario: Лише активні

- **WHEN** клієнт `GET /tc-projects?active=active`
- **THEN** повертаються лише проекти з `is_archived = false`

#### Scenario: Лише архівні

- **WHEN** клієнт `GET /tc-projects?active=inactive`
- **THEN** повертаються лише проекти з `is_archived = true`

#### Scenario: Усі (дефолт)

- **WHEN** клієнт `GET /tc-projects` без параметра `active`
- **THEN** повертаються усі проекти незалежно від `is_archived`

#### Scenario: Невалідне значення фільтра

- **WHEN** клієнт `GET /tc-projects?active=foo`
- **THEN** відповідь `422 Unprocessable Entity`

