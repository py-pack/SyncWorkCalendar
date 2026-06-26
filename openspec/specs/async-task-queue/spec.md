# async-task-queue Specification

## Purpose
TBD - created by archiving change add-celery-auto-linking. Update Purpose after archive.
## Requirements
### Requirement: Черга задач на Celery + Redis

Система SHALL надавати тривку чергу задач на базі `Celery` з брокером `Redis`.
Sync-операції (`TimeCampUpdateTask`, `UpdateJiraTask`, `WorllogSyncTask` та
реконсиляція лінків) MUST бути доступні як Celery-таски, що виконуються у
воркер-процесі окремо від `api`. Кожна Celery-таска MUST переюзовувати наявний
`api_jobs`-аудит (життєвий цикл `running → needs_verification | failed`), тож
постановка через чергу й через HTTP-тригер дають однаковий слід у `api_jobs`.
Конфіг брокера береться з `APP__REDIS__URL` (дефолт `redis://redis:6379/0`).

#### Scenario: Таска виконується воркером і пише в api_jobs

- **WHEN** у чергу ставиться Celery-таска синку (напр. витяг Tempo-worklog-ів)
- **THEN** воркер виконує її поза процесом `api`, а в `api_jobs` зʼявляється рядок,
  що проходить `running → needs_verification` на успіху або `running → failed` на
  виключенні

#### Scenario: Брокер недоступний

- **WHEN** `Redis` недоступний у момент постановки таски
- **THEN** постановка завершується помилкою, яку викликач отримує явно (HTTP-тригер
  повертає помилку), а не «тихо» втрачає завдання

### Requirement: Планувальник beat — щодобовий витяг і реконсиляція

Система SHALL запускати `Celery beat` як **окремий** процес/контейнер, що за
розкладом ставить у чергу планові задачі:

- `01:00` — синк TimeCamp-записів за останній період і витяг останніх Jira-задач;
- `01:30` — витяг усіх Tempo-worklog-ів (`jr_worklogs`) за останній період;
- після кожного витягу — `reconcile_links` (матчинг + постановка пушу/оновлення).

Beat MUST бути єдиним екземпляром (щоб розклад не дублювався). Часи розкладу —
**фіксовані константи**; конфігурується лише **таймзона** через
`APP__CELERY__TIMEZONE` (дефлот `UTC` = UTC+0; усі часи в UTC).

#### Scenario: Щодобовий тік ставить задачі в чергу

- **GIVEN** `beat` запущено
- **WHEN** настає запланований час (`01:00` за `APP__CELERY__TIMEZONE`)
- **THEN** у чергу потрапляють задачі витягу TimeCamp + Jira, а о `01:30` — витягу
  Tempo; після кожного витягу — `reconcile_links`

#### Scenario: Beat поважає per-user перемикачі

- **GIVEN** користувач має вимкнений прапор автосинку (напр. `auto_tempo_pull = false`)
- **WHEN** beat формує планові задачі
- **THEN** для цього користувача відповідна задача **не** ставиться в чергу

### Requirement: Воркер і beat — окремі контейнери на образі бекенду

Воркер і планувальник Celery SHALL запускатись як окремі docker-сервіси на тому самому образі, що `api`, без exposed-портів, із залежністю від `redis` і `db`. Воркер — команда `celery -A app.celery_app worker`, планувальник — `celery -A app.celery_app beat`. Суміщений режим `worker -B` MUST NOT використовуватись у не-дев конфігурації.

#### Scenario: Стек піднімає worker і beat

- **WHEN** виконується `docker compose up`
- **THEN** піднімаються сервіси `redis`, `worker`, `beat` (на додачу до `db`/`api`/
  `front`), причому `beat` — рівно в одному екземплярі

### Requirement: Планове прибирання журналу `api_jobs`

Система SHALL запускати з `Celery beat` окрему **maintenance**-таску прибирання
`api_jobs`, що за щодобовим розкладом (фіксована константа, після нічних синків —
напр. `02:00` за `APP__CELERY__TIMEZONE`) виконує два кроки:

1. **авто-verify** старих `needs_verification` (старших за `APP__CELERY__AUTO_VERIFY_DAYS`,
   дефолт `7`) → `verified` із `verified_by = "system"`;
2. **TTL-видалення** термінальних (`verified`/`failed`) рядків, старших за
   `APP__CELERY__JOB_TTL_DAYS` (дефолт `90`).

Ця таска MUST **не** створювати власний `api_jobs`-аудит-рядок (на відміну від
sync-тасок) — інакше maintenance плодила б job-и, які сама ж чистить; вона лише
логує кількість авто-verify-нутих і видалених. Per-user `sync_prefs` тут **не**
застосовні (це глобальне прибирання, не per-user синк).

#### Scenario: Щодобовий тік прибирає журнал

- **GIVEN** `beat` запущено
- **WHEN** настає запланований час прибирання
- **THEN** у чергу стає maintenance-таска, яка авто-verify-ить старі
  `needs_verification` і видаляє старі термінальні рядки згідно з налаштованими TTL

#### Scenario: Maintenance-таска не засмічує журнал

- **WHEN** maintenance-таска виконується
- **THEN** у `api_jobs` **не** з'являється новий рядок про саму таску прибирання

