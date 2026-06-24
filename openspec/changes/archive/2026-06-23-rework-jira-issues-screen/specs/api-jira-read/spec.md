## MODIFIED Requirements

### Requirement: Список Jira-задач

Система SHALL надавати `GET /jr-issues`, що повертає збережені `jr_issues` за
період **активності** із локальної БД, **сторінковано** (`{ items, total }`,
прецедент `TCEntriesResponse`/`GET /api-jobs`), із фільтрами за проектом,
статусом і пошуком за назвою. Endpoint MUST вимагати валідний Bearer-токен.
Модель `JRIssue` уже існує — додаються лише параметри запиту, пагінація й похідне
поле; **без alembic-міграції**.

Параметри запиту:

- `updated_from`, `updated_to` (date) — період за `jr_issues.updated_at` (дата
  **оновлення/активності** задачі, не створення — щоб показувати задачі, з якими
  працювали у вікні, незалежно від дати створення). Якщо не задані — дефолт
  **поточний місяць** (перше … останнє число). `updated_from` MUST бути
  `<= updated_to`, інакше `400 Bad Request`.
- `project_id` — `int | null`: фільтр за `jr_projects.id`.
- `status` — `str | null`: **точний** фільтр за `jr_issues.status` (наприклад,
  `In Progress`). Якщо не задано — статус не фільтрується.
- `q` — `str | null`: case-insensitive пошук (`ILIKE %q%`) по `key` **або** `name`.
- `limit` (дефолт `50`, максимум `200`), `offset` (дефолт `0`).

Відповідь — обʼєкт `{ items, total }`, де кожен `item` — `JRIssueItem` із наявними
полями (`id`, `key`, `name`, `jr_project_id`, `type`, `priority`, `status`,
`epic_key`, `parent_key`, `estimate_plan`/`fact`/`rest`) і похідним прапором
`active`:

- `active` — `true`, якщо `status` **не** в «done»-сеті
  (`done`/`closed`/`resolved`/`cancelled`/локалізовані відповідники); інакше `false`.
  Сирий `status` лишається у відповіді.
- `total` — кількість задач за тим самим фільтром (період + `project_id` + `status`
  + `q`), без урахування `limit`/`offset`.

Задачі MUST сортуватися за `updated_at` спадно (`NULL` — останніми).

#### Scenario: Дефолтний період і пагінація

- **WHEN** авторизований клієнт `GET /jr-issues` без параметрів
- **THEN** повертаються задачі, **оновлені** в поточному місяці, відсортовані за
  `updated_at` спадно, не більше `50` у `items`, із повним `total` за період

#### Scenario: Фільтр за проектом

- **WHEN** клієнт `GET /jr-issues?project_id=7`
- **THEN** повертаються лише задачі проекту з `jr_project_id = 7` (у межах періоду)

#### Scenario: Фільтр за статусом

- **GIVEN** є задачі зі статусами `In Progress` і `Done`
- **WHEN** клієнт `GET /jr-issues?status=In%20Progress`
- **THEN** у `items` присутні лише задачі зі `status = "In Progress"`

#### Scenario: Пошук за ключем або назвою

- **WHEN** клієнт `GET /jr-issues?q=login`
- **THEN** повертаються задачі, чий `key` **або** `name` містить `login`
  (case-insensitive), у межах періоду

#### Scenario: Фільтр за періодом активності

- **GIVEN** задача `LDI-7` має `updated_at` у березні, а `LDI-9` — у травні
- **WHEN** клієнт `GET /jr-issues?updated_from=2026-05-01&updated_to=2026-05-31`
- **THEN** у `items` присутня `LDI-9` і відсутня `LDI-7` (незалежно від дат їх
  створення)

#### Scenario: Пагінація — total незалежний від limit/offset

- **WHEN** клієнт `GET /jr-issues?limit=10&offset=20`
- **THEN** `items` містить не більше `10` задач, починаючи зі зміщення `20`, а
  `total` дорівнює повній кількості задач за фільтром

#### Scenario: Похідний прапор активності

- **GIVEN** задача `LDI-9` має статус `Done`
- **WHEN** клієнт `GET /jr-issues?q=LDI-9`
- **THEN** відповідний елемент має `active = false`

#### Scenario: Валідація періоду

- **WHEN** клієнт `GET /jr-issues?updated_from=2026-05-31&updated_to=2026-05-01`
- **THEN** відповідь `400 Bad Request` із `detail` про `start must be <= end`

#### Scenario: Без токена

- **WHEN** клієнт `GET /jr-issues` без `Authorization`
- **THEN** відповідь `401 Unauthorized`

## ADDED Requirements

### Requirement: Перелік статусів Jira-задач

Система SHALL надавати `GET /jr-issues/statuses`, що повертає список **усіх
наявних у БД** значень `jr_issues.status` (distinct), для наповнення випадайки
фільтра статусу на екрані Jira. Endpoint MUST вимагати валідний Bearer-токен.

- Відповідь — `list[str]` унікальних статусів, відсортованих за абеткою.

#### Scenario: Перелік усіх статусів

- **WHEN** авторизований клієнт `GET /jr-issues/statuses`
- **THEN** відповідь `200 OK` зі списком унікальних статусів, наявних у `jr_issues`

#### Scenario: Без токена

- **WHEN** клієнт `GET /jr-issues/statuses` без `Authorization`
- **THEN** відповідь `401 Unauthorized`
