## ADDED Requirements

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
