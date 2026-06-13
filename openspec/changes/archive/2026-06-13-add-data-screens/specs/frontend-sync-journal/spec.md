## ADDED Requirements

### Requirement: Таблиця журналу синхронізацій

Екран «Журнал синку» SHALL показувати рядки `api_jobs` (`GET /api-jobs`) із
колонками: `id`, тригер, статус (бейдж; `running` зі спінером), старт,
запустив, дія. Журнал MUST мати фільтри за статусом (усі /
`needs_verification` / `failed` / `running`). Рядок MUST бути клікабельним і
відкривати деталі.

#### Scenario: Фільтр за статусом

- **WHEN** користувач обирає фільтр `needs_verification`
- **THEN** у таблиці лишаються лише jobs зі статусом `needs_verification`

#### Scenario: Статус running

- **WHEN** job має статус `running`
- **THEN** бейдж показує спінер і підпис «Виконується»

### Requirement: Деталі job у бічній панелі

Клік по рядку SHALL відкривати бічну панель (`Sheet`) із деталями job
(`GET /api-jobs/{id}`): тригер, статус, хто запустив, старт/фініш, хто і коли
підтвердив, а також `payload`, `result` і `error` як форматований JSON. Блок
`error` MUST візуально виділятися.

#### Scenario: Перегляд payload/result

- **WHEN** користувач відкриває деталі завершеного job
- **THEN** показуються `payload` і `result` як читабельний JSON

#### Scenario: Job з помилкою

- **WHEN** job має `error`
- **THEN** у деталях показується виділений блок помилки

### Requirement: Підтвердження needs_verification

Для job у стані `needs_verification` журнал SHALL показувати кнопку
«Підтвердити» (у рядку і в деталях), що викликає
`POST /api-jobs/{id}/verify`. Після підтвердження статус MUST оновитися на
`verified` без перезавантаження сторінки.

#### Scenario: Підтвердження job

- **WHEN** користувач натискає «Підтвердити» на job `needs_verification`
- **THEN** виконується `POST /api-jobs/{id}/verify`, статус стає `verified`,
  кнопка зникає

#### Scenario: Бейдж навігації

- **WHEN** є непідтверджені jobs (`needs_verification`)
- **THEN** пункт «Журнал синку» в навігації показує лічильник таких jobs
