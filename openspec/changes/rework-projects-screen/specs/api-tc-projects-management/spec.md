## ADDED Requirements

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
