## ADDED Requirements

### Requirement: Запуск синку «зараз» із закладки «Синхронізації»

Закладка «Синхронізації» SHALL надавати напроти **кожного** тумблера
`sync_prefs` (`auto_timecamp_pull`, `auto_jira_pull`, `auto_tempo_pull`,
`auto_linking`, `auto_push_tempo`) кнопку **«Запустити зараз»**, що відкриває
**спільний** попап вибору періоду. Попап MUST містити `PeriodPicker` із дефолтом
**«цей місяць»** (`syncPeriod()`) і запускати **наявний** sync-тригер, що
відповідає тумблеру:

- `auto_timecamp_pull` → `POST /sync/timecamp/projects`, далі
  `POST /sync/timecamp/entries`
- `auto_jira_pull` → `POST /sync/jira/projects`, далі `POST /sync/jira/issues-all`
- `auto_tempo_pull` → `POST /sync/jira/worklogs`
- `auto_linking` → `POST /sync/reconcile-links`
- `auto_push_tempo` → `POST /sync/worklog-tasks/push-to-tempo`

Виконання MUST бути **синхронним** (як попапи `SyncEntriesModal`/
`PullWorklogsModal`): кнопка показує спінер до завершення, далі попап показує
**результат-дельту** або повідомлення про помилку. Виняток — `auto_linking`, що
за контрактом `api-sync-triggers` лише **ставиться в чергу** (`202`); для нього
попап MUST показати, що дію поставлено в чергу (результат — у Журналі синку), і
закритись. Команди TimeCamp/Jira MUST викликати **обидва** тригери послідовно
(спершу проекти, потім дані за період); помилка синку проектів зупиняє дію до
запиту даних. Жоден нинішній тригер контрактно НЕ змінюється; нові ендпоінти НЕ
вводяться. Спільні `SyncState`/`SyncFilter` («мова синку») тут НЕ застосовуються.

#### Scenario: Запуск синку TimeCamp за період

- **WHEN** користувач тисне «Запустити зараз» напроти `auto_timecamp_pull`,
  обирає період і підтверджує
- **THEN** послідовно викликаються `POST /sync/timecamp/projects` і
  `POST /sync/timecamp/entries` за обраний період; на час виконання кнопка
  показує спінер, на успіх попап показує дельту, на помилку — повідомлення без
  закриття

#### Scenario: Запуск реконсиляції лінків (enqueue)

- **WHEN** користувач тисне «Запустити зараз» напроти `auto_linking`, обирає
  період і підтверджує
- **THEN** викликається `POST /sync/reconcile-links` (відповідь `202`); попап
  повідомляє, що дію поставлено в чергу (результат — у Журналі синку), і
  закривається

#### Scenario: Дія без налаштованого worker_key

- **GIVEN** користувач без `worker_key`
- **WHEN** він запускає дію, що потребує `worker_key` (`auto_tempo_pull`,
  `auto_linking` або `auto_push_tempo`)
- **THEN** показується зрозуміла помилка (бек віддає
  `400 "user has no worker_key configured"`), синк не виконується

#### Scenario: Дефолтний період попапа

- **WHEN** користувач відкриває попап «Запустити зараз» для будь-якого тумблера
- **THEN** період попередньо встановлено на «цей місяць» (`syncPeriod()`), з
  можливістю змінити через `PeriodPicker`
