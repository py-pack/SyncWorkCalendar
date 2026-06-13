## MODIFIED Requirements

### Requirement: Список Jira-задач

Система SHALL надавати `GET /jr-issues`, що повертає збережені `jr_issues` із
полями `key`, `name`/summary, `status`, проект (через `jr_project_id`/префікс
ключа) і похідним прапором `active`. Endpoint MUST підтримувати фільтр за
проектом (`project_id`), **пошук** `q` і **обмеження** `limit`, та вимагати
валідний Bearer-токен. Модель `JRIssue` уже існує — додаються лише параметри
запиту й похідне поле.

- `q` — `str | null`: case-insensitive пошук (`ILIKE %q%`) по `key` **або**
  `name`. За наявності `q` результати сортуються `updated_at DESC` («останні за
  релевантністю до пошуку»).
- `limit` — `int | null`: максимальна кількість елементів у відповіді (дефолт
  `10`, капується значенням `≤ 50`). Призначений для select-а з пошуком, щоб не
  віддавати всі задачі одразу.
- `active` — `bool` у кожному елементі: `true`, якщо `status` **не** в «done»-сеті
  (`done`/`closed`/`resolved`/`cancelled`/локалізовані відповідники);
  `false` — інакше. Сирий `status` лишається у відповіді.

#### Scenario: Перегляд задач

- **WHEN** авторизований клієнт `GET /jr-issues`
- **THEN** відповідь `200 OK` зі списком задач (ключ, назва, статус, `active`),
  не більше `limit` (дефолт 10) елементів

#### Scenario: Фільтр за проектом

- **WHEN** клієнт `GET /jr-issues?project_id=7`
- **THEN** повертаються лише задачі проекту з `jr_project_id = 7`

#### Scenario: Пошук за ключем або назвою

- **WHEN** клієнт `GET /jr-issues?q=login&limit=10`
- **THEN** повертаються до 10 задач, чий `key` **або** `name` містить `login`
  (case-insensitive), відсортованих за `updated_at DESC`

#### Scenario: Похідний прапор активності

- **GIVEN** задача `LDI-9` має статус `Done`
- **WHEN** клієнт `GET /jr-issues?q=LDI-9`
- **THEN** відповідний елемент має `active = false`

#### Scenario: Капування limit

- **WHEN** клієнт `GET /jr-issues?limit=9999`
- **THEN** кількість елементів у відповіді не перевищує верхню межу (`50`)

#### Scenario: Без токена

- **WHEN** клієнт `GET /jr-issues` без `Authorization`
- **THEN** відповідь `401 Unauthorized`
