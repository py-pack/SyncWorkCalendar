## ADDED Requirements

### Requirement: Список Jira-задач

Система SHALL надавати `GET /jr-issues`, що повертає збережені `jr_issues` із
полями `key`, `name`/summary, `status`, проект (через `jr_project_id`/префікс
ключа) і лічильником worklog-ів (за наявності). Endpoint MUST підтримувати
фільтр за проектом (`project`/`project_key`) і вимагати валідний Bearer-токен.
Модель `JRIssue` уже існує — додається лише endpoint читання.

#### Scenario: Перегляд задач

- **WHEN** авторизований клієнт `GET /jr-issues`
- **THEN** відповідь `200 OK` зі списком задач (ключ, статус, проект)

#### Scenario: Фільтр за проектом

- **WHEN** клієнт `GET /jr-issues?project=OCT`
- **THEN** повертаються лише задачі проекту `OCT`

#### Scenario: Без токена

- **WHEN** клієнт `GET /jr-issues` без `Authorization`
- **THEN** відповідь `401 Unauthorized`

### Requirement: Тогл `is_watched` для Jira-проекту

Система SHALL надавати `PATCH /jr-projects/{id}`, що змінює локальний прапор
`is_watched`. Відсутній `id` → `404`. Інші поля проекту (синхронізовані з
Jira) через цей endpoint MUST NOT змінюватися.

#### Scenario: Увімкнення відстеження

- **WHEN** клієнт `PATCH /jr-projects/{id}` із `is_watched=true`
- **THEN** відповідь `200 OK`; наступний `GET /jr-projects` повертає проект
  із `is_watched=true`

#### Scenario: Відсутній проект

- **WHEN** клієнт `PATCH /jr-projects/{id}` для неіснуючого `id`
- **THEN** відповідь `404 Not Found`
