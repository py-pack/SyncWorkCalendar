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
