# api-sync-status Specification

## Purpose

Read-only status endpoints that expose sync metadata: TC/Jira projects with
their flags and counts, worklog sync task aggregations, and untracked TC
entries. Period-based endpoints share consistent validation.

## Requirements

### Requirement: List TC projects with sync metadata

Система SHALL надавати `GET /tc-projects` з опційними query-параметрами
`?start=<ISO date>&end=<ISO date>` (дефолт — поточний місяць у UTC).
Відповідь SHALL містити список усіх записів `tc_projects` + лічильник
`tc_entries` за вказаний період.

#### Scenario: Default period returns all projects

- **WHEN** клієнт `GET /tc-projects` без параметрів
- **THEN** відповідь `200 OK` із масивом `[{id, name, is_sync, issue_key, is_archived, entries_count}]`, де
  `entries_count` — кількість `tc_entries.start_at` у `[поч. місяця, кін. місяця]`

#### Scenario: Custom period filters entries count

- **WHEN** клієнт `GET /tc-projects?start=2026-04-01&end=2026-04-30`
- **THEN** `entries_count` у кожному елементі рахується за період `2026-04-01 00:00 .. 2026-04-30 23:59` по
  `tc_entries.start_at`

#### Scenario: Invalid date format

- **WHEN** клієнт передає `start=not-a-date`
- **THEN** відповідь `422 Unprocessable Entity` із FastAPI-валідаційним detail

### Requirement: List Jira projects with sync metadata

Система SHALL надавати `GET /jr-projects`. Відповідь SHALL містити список `jr_projects` із поточними прапорами та
кількістю пов'язаних `jr_issues`.

#### Scenario: Default response

- **WHEN** клієнт `GET /jr-projects`
- **THEN** відповідь `200 OK` із масивом `[{id, key, name, is_archived, is_watched, issues_count}]`, де `issues_count` —
  `COUNT(*) FROM jr_issues WHERE jr_project_id = <id>`

### Requirement: Worklog sync tasks status overview

Система SHALL надавати `GET /worklog-sync-tasks` з обов'язковим періодом-фільтром і опційним `?status=<StatusTaskEnum>`.
Відповідь SHALL містити агрегацію по статусах + сам перелік задач за період.

#### Scenario: Aggregation per status

- **WHEN** клієнт `GET /worklog-sync-tasks?start=2026-04-01&end=2026-04-30`
- **THEN** відповідь `200 OK` із тілом
  `{summary: {pre_create: <int>, create: <int>, created: <int>, ...}, items: [<WorklogSyncTaskDTO>]}`, де `summary`
  рахує `worklog_sync_tasks.status` за `started_at` у періоді

#### Scenario: Filter by single status

- **WHEN** клієнт додає `&status=create`
- **THEN** `items` містить лише задачі зі `status = create`; `summary` залишається повним по всіх статусах періоду

#### Scenario: Empty period

- **WHEN** період не має жодного `worklog_sync_tasks` запису
- **THEN** відповідь `200 OK` із `{summary: {<all enum keys>: 0}, items: []}`

### Requirement: Untracked TC entries lookup

Система SHALL надавати `GET /tc-entries/untracked` із обов'язковим періодом. Відповідь — entries без `meta.task` і без
матчу через `tc_projects.issue_key` батьківського проекту, тобто ті, що не зможуть створити worklog без ручного
втручання.

#### Scenario: Entry without meta and project issue_key

- **GIVEN** `tc_entries.meta IS NULL` і `tc_projects.issue_key IS NULL` для батьківського `tc_project_id`
- **WHEN** клієнт `GET /tc-entries/untracked?start=2026-04-01&end=2026-04-30`
- **THEN** entry присутній у відповіді з полями `{id, description, start_at, end_at, tc_project_id, tc_project_name}`

#### Scenario: Entry resolved via project fallback

- **GIVEN** `tc_entries.meta IS NULL`, але `tc_projects.issue_key = 'LDI-42'`
- **WHEN** клієнт `GET /tc-entries/untracked` за той самий період
- **THEN** entry **не** включається у відповідь (fallback покриє його при синку)

#### Scenario: Entry has meta task

- **GIVEN** `tc_entries.meta = {"task": "LDI-7"}`
- **WHEN** клієнт `GET /tc-entries/untracked`
- **THEN** entry **не** включається у відповідь

### Requirement: Period validation across status endpoints

Усі status-endpoint-и із параметром періоду SHALL відмовляти при `start > end` з `400 Bad Request` і
`detail: "start must be <= end"`.

#### Scenario: Inverted period

- **WHEN** клієнт `GET /worklog-sync-tasks?start=2026-04-30&end=2026-04-01`
- **THEN** відповідь `400 Bad Request` із `{detail: "start must be <= end"}`
