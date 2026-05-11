# Інтеграція з Jira і Tempo Timesheets

Технічна довідка по інтеграції з `Jira on-prem` та плагіном `Tempo
Timesheets` станом на 2026-05-11. Описує HTTP-клієнт, DTO, ORM-моделі,
DAO, оркестрацію тасків, state-machine `WorllogSyncTask`, парсинг опису
worklog-а та повну схему таблиць БД.

## 1. Огляд

`Jira` — внутрішня on-prem інсталяція `leadsdoit.io/jira`. Інтеграція
**двостороння**:

- **Читання:** проекти, issues, worklog-и (через плагін Tempo) тягнуться
  у локальну БД (`jr_*` таблиці).
- **Запис:** worklog-и створюються в `Tempo` через POST API. Локальна
  таблиця `worklog_sync_tasks` тримає чергу/журнал цих створень.

Парність із `TimeCamp` інтеграцією — TimeCamp дає `entries`, Jira дає issue
keys, `worklog_sync_tasks` пов'язує одне з одним і пушить у Tempo. Деталі
парного боку — `timecamp.md`. Сам конвеєр і модель сихронізації — у
`../../memory-bank/systemPatterns.md` і нижче в §8.

## 2. Зовнішні API

**Base URL:** `https://leadsdoit.io/jira/rest/`
**Auth:** заголовок `Authorization: Bearer <APP__JIRA__TOKEN>`
**Транспорт:** `requests` (синхронний). Усе йде через
`JiraService._make_request` (`src/services/jira/jira_service.py:147`).

| Метод | Endpoint                              | Призначення                                            | Метод-обгортка                            |
| ----- | ------------------------------------- | ------------------------------------------------------ | ----------------------------------------- |
| GET   | `api/2/project`                       | Список усіх проектів акаунту                           | `JiraService.get_projects` (`:13`)        |
| POST  | `api/2/search`                        | Issues за JQL (`key in (...)`)                         | `JiraService.search_issues` (`:23`)       |
| POST  | `tempo-timesheets/4/worklogs/search`  | Worklog-и за датами і користувачем                     | `JiraService.serch_worklogs_by_user` (`:103`, typo в назві) |
| POST  | `tempo-timesheets/4/worklogs`         | Створення worklog-а в Tempo                            | `JiraService.create_worklog` (`:130`)     |

`api/2` — рідне Jira REST API. `tempo-timesheets/4` — окремий API плагіна
Tempo, який живе в тому самому домені, але має іншу схему запитів і
структуру об'єктів (`originId`, `originTaskId`, `worker`, `timeSpentSeconds`).

### Обробка помилок

`_make_request` (`:147-175`) ловить **усі** `requests.RequestException` і
друкує їх у stdout, повертаючи `{}`. Наслідки для викликачів:

- `search_issues`: `{}.get('issues') → None → return []`. Тихо.
- `serch_worklogs_by_user`: `{}` ітерується як порожній dict, list-comprehension
  дає `[]`. Тихо.
- `create_worklog`: робить `dict(worklogs[0])` — на `{}` це підніме
  `KeyError`. **Помилки Tempo пробиваються через виключення**, а не через
  empty-return.

Тип-анотація `-> dict` на `_make_request` бреше: для search/worklogs реальна
відповідь — `list`.

---

## 3. DTO (Pydantic v2)

`src/services/jira/dto.py`:

```text
JiraProjectDTO   — id, key, name, is_archved
JiraUserDTO      — key, name, full_name, email
JiraIssueDTO     — id, key, name, jr_project_id, epic_key, parent_key,
                   type, priority, status, jr_creator_key, jr_reporter_key,
                   estimate_plan, estimate_fact, estimate_rest,
                   created_at, updated_at,
                   project (вкладений), creator, reporter
JiraWorklogDTO   — id, jr_issues_id, jr_issues_key, description,
                   jr_worker_key, started_at, duration,
                   created_at, updated_at, issue (вкладений)
```

Усі мають `Config.from_attributes = True` — створюються з ORM.

`field_validator(..., mode='before')`:
- `id`, `jr_project_id`, `jr_issues_id` — каст у `int`; `≤ 0` → `None`.
- `estimate_plan/fact/rest` — каст у `int`; `None` → `0`.

**Маппінг із Jira API → DTO** (`JiraService.search_issues`, `:35-99`):

| Jira `fields.*`                       | DTO поле                  |
| ------------------------------------- | ------------------------- |
| `summary`                             | `name`                    |
| `issuetype.name`                      | `type` (дефолт `'Task'`)  |
| `priority.name`                       | `priority` (`'Medium'`)   |
| `status.name`                         | `status` (`'To DO'`)      |
| `created`, `updated`                  | `created_at`, `updated_at`|
| `customfield_10005`                   | `epic_key`                |
| `parent.key`                          | `parent_key`              |
| `timeoriginalestimate` (sec)          | `estimate_plan`           |
| `aggregateprogress.progress` (sec)    | `estimate_fact`           |
| `aggregatetimeestimate` (sec)         | `estimate_rest`           |
| `project.{id,key,name}`               | вкладений `JiraProjectDTO`|
| `creator.{key,name,displayName,email}`| вкладений `JiraUserDTO`   |
| `reporter.{key,...}`                  | вкладений `JiraUserDTO`   |

**Маппінг Tempo → DTO** (`serch_worklogs_by_user`, `:116-126`):

| Tempo response                  | DTO поле          |
| ------------------------------- | ----------------- |
| `originId`                      | `id`              |
| `originTaskId`                  | `jr_issues_id`    |
| `issue.key`                     | `jr_issues_key`   |
| `comment`                       | `description`     |
| `worker`                        | `jr_worker_key`   |
| `started`                       | `started_at`      |
| `timeSpentSeconds`              | `duration`        |
| `dateCreated`, `dateUpdated`    | `created_at`, `updated_at` |

---

## 4. Потік даних

```
UpdateJiraTask  (src/tasks/jira_update_task.py)
   ├─ update_all_projects()
   │      JiraService.get_projects        → JRProjectDAO.sync_all
   │
   ├─ update_jira_issues(keys: list|set)
   │      JiraService.search_issues       → JRIssuesDAO.sync_by_key
   │      (каскадно записує users, projects, issues)
   │
   └─ update_worklog(start, end)
          JiraService.serch_worklogs_by_user(start, end, settings.current_user)
              → JRWorklogDAO.sync_all_between(...)
              → UpdateJiraTask.update_jira_issues(<unique issue keys>)
                (рефреш issue-метаданих по тих, що з'явились у worklog)


WorllogSyncTask  (src/tasks/worllog_sync_task.py)         ← state machine
   ├─ create_task_for_sync(start, end)
   │      TCEntriesDAO.get_entries_for_worklogs(...) →
   │      для кожного entry: якщо WorklogSyncTask з таким source_id ще нема —
   │      створити з статусом pre_create.
   │
   ├─ before_create(start, end)
   │      WorklogSyncTaskDAO.get_by_period_and_status(pre_create)
   │      → перевірити issue_keys у локальній БД
   │      → відсутні підтягнути через UpdateJiraTask.update_jira_issues
   │      → проставити task.issue_id, status = create
   │
   └─ create_worklogs(start, end)
          WorklogSyncTaskDAO.get_by_period_and_status(create)
          → для кожного: JiraService.create_worklog(...)
          → task.target_id = result['originId'], status = created
```

---

## 5. ORM-моделі

Усі — `src/models/jr_*.py`, наслідують `Base` (snake-case + `s` →
`jr_projects`, `jr_users`, `jr_issues`, `jr_worklogs`). Жодного FK
оголошеного. Повний DDL — `../database/schema.md` §3.

### `JRProject` (`src/models/jr_project.py:7`)

```text
key         : String UNIQUE NOT NULL    — project key з Jira (LDI, PEG, ...)
name        : String NOT NULL
is_archved  : Boolean NOT NULL DEFAULT FALSE   — ⚠ typo, див. §10
is_watched  : Boolean NOT NULL DEFAULT TRUE    — локальний прапор: чи тягнути цей проект у синк
```

### `JRUser` (`src/models/jr_user.py:6`)

```text
key        : String UNIQUE NOT NULL     — Jira username/account-key
name       : String NULL
full_name  : String NULL                — Jira displayName
email      : String NULL
```

### `JRIssue` (`src/models/jr_issue.py:9`)

```text
key                : String UNIQUE NOT NULL    — Jira issue key (LDI-123)
name               : String NOT NULL           — summary
jr_project_id      : Integer NOT NULL, indexed — soft FK → jr_projects.id
epic_key           : String NULL, indexed      — customfield_10005 з Jira
parent_key         : String NULL, indexed
type               : String NOT NULL           — Task / Bug / Story / ...
priority           : String NOT NULL
status             : String NOT NULL
jr_creator_key     : String NULL, indexed      — soft FK → jr_users.key
jr_reporter_key    : String NULL, indexed
estimate_plan      : Integer NOT NULL DEFAULT 0  — секунди, timeoriginalestimate
estimate_fact      : Integer NOT NULL DEFAULT 0  — секунди, aggregateprogress.progress
estimate_rest      : Integer NOT NULL DEFAULT 0  — секунди, aggregatetimeestimate
created_at         : TIMESTAMPTZ DEFAULT now()
updated_at         : TIMESTAMPTZ DEFAULT now()
```

Жодних event-listener-ів.

### `JRWorklog` (`src/models/jr_worklog.py:11`)

```text
jr_issues_id    : Integer NOT NULL, indexed    — ⚠ ім'я з зайвою 's', див. §10
description     : String NOT NULL              — сирий текст worklog-а
meta            : JSON NULL                    — заповнюється event-listener-ом
jr_worker_key   : String NULL, indexed         — soft FK → jr_users.key
started_at      : TIMESTAMPTZ NOT NULL
duration        : Integer NOT NULL DEFAULT 0   — секунди
created_at      : TIMESTAMPTZ DEFAULT now()
updated_at      : TIMESTAMPTZ DEFAULT now()
```

**Event-listener `'set'` на `description`** (`change_to_description`,
`:24-49`) — див. §7.

---

## 6. DAO-шар

### `JRProjectDAO` (`src/dao/jr_project_dao.py:8`)

- `model = JRProject`.
- `all_keys_sync()` (`:12`) — **синхронний** SELECT усіх `key`. Викликається
  з `SyncTaskService` для кешу (event-листенер у `tc_entry` не може робити
  `await`). Решта операцій — успадковані з `BaseDAO`.

### `JRUsersDAO` (`src/dao/jr_users_dao.py:5`)

- `model = JRUser`. Без своїх методів — лише `BaseDAO.update_by_keys` тощо.

### `JRIssuesDAO` (`src/dao/jr_issues_dao.py:12`)

- `sync_by_key(db, issues: List[JiraIssueDTO])` (`:15`) — **каскадне
  оновлення**:
  1. Збирає унікальні `creator`/`reporter` із вкладених `JiraUserDTO` → `JRUsersDAO.update_by_keys(..., key_sync='key')`.
  2. Збирає `project` із вкладених `JiraProjectDTO` → `JRProjectDAO.update_by_keys(..., key_sync='key')`.
  3. Потім сам `update_by_keys(db, issues)` для `jr_issues`.
  - **Не** використовує `sync_all` (без full-replace) — issues тільки апсертяться, чужі рядки лишаються.
  - ⚠ Дрібний баг копі-пасту: проекти збираються через `if users.get(issue.project.key) is None` (`:27`) — перевіряється не той dict. Працює тільки тому, що ключі проектів і користувачів не перетинаються.
- `get_in_keys(db, keys)` (`:42`, `@classmethod`) — `SELECT id, key WHERE key IN (...)`. Повертає `list[RowMapping]`. Використовується в `WorllogSyncTask.before_create` для резолву `issue_key → issue_id`.

### `JRWorklogDAO` (`src/dao/jr_worklog_dao.py:8`)

- `sync_all_between(db, worklogs, date_from, date_to)` (`:12`, `@classmethod`) —
  період-обмежений full-replace: тягне існуючі worklog-и з БД, де
  `started_at` у `[date_from 00:00, date_to 23:59]`, і викликає
  `_sync(db, new, existing)` (з `BaseDAO`). DELETE обмежений діапазоном,
  щоб не зачепити інші місяці.

### `WorklogSyncTaskDAO` (`src/dao/worklog_sync_task_dao.py:10`)

- `get_by_period_and_status(db, start, end, status: StatusTaskEnum | None)`
  (`:14`, `@classmethod`) — SELECT за `started_at IN [start, end]`, опційно
  з фільтром `status`. Повертає `list[WorklogSyncTask]`.

---

## 7. Парсинг `description` → `meta` (`JRWorklog`)

`change_to_description` (`src/models/jr_worklog.py:24-46`, event listener
`'set'` на `JRWorklog.description`):

1. Запускається на кожен `worklog.description = ...`.
2. Регулярка:

   ```
   sync\|(?P<start_time>\d{2}:\d{2})\|(?P<end_time>\d{2}:\d{2})[\-_| ]{1,3}(?P<content>.*)
   ```

   Очікує формат `sync|HH:MM|HH:MM - <content>` (роздільник `-`, `_`, `|` або пробіл, 1–3 символи).
3. Якщо матч є — у `target.meta` записує:
   - `start_time`, `end_time` — рядки `HH:MM`.
   - `content` — текст після часу.
4. Якщо матча нема — `target.meta = {'content': value}` (просто опис).

Цей же формат **генерує** `TCEntriesDAO._create_content_by_template`, коли
`worklog_sync_tasks.content` будується для Tempo (`integrations/timecamp.md`
§6). Тобто опис worklog-а в Tempo навмисно структурований так, щоб
імпорт зворотньо розпарсив часи.

---

## 8. State machine — `WorllogSyncTask`

Клас-orchestrator: `src/tasks/worllog_sync_task.py:15`
(typo `Worllog` свідомо збережена в коді — див. §10).

```
[TC entry в період]
       ↓ create_task_for_sync()
  [pre_create]
       ↓ before_create()
       │  - перевірити, що issue_key є в jr_issues; якщо нема —
       │    UpdateJiraTask.update_jira_issues(missing_keys)
       │  - проставити task.issue_id
       ↓
  [create]
       ↓ create_worklogs()
       │  - JiraService.create_worklog(...)
       │  - task.target_id = result['originId']
       ↓
  [created]
```

Енам `StatusTaskEnum` (`src/models/worklog_sync_task.py:12-19`) містить також
`pre_update`, `update`, `updated`, `sync` — **не використовуються**.
Зарезервовано для майбутнього потоку синхронізації **оновлень** worklog-ів,
коли TC entry змінився після створення.

`before_insert`/`before_update`-хук `set_created_at` (`:38-44`) ставить
`created_at` при першому збереженні та `updated_at = now(UTC)` на кожен
update.

---

## 9. Конфігурація

`src/config.py`:

- `Settings.jira: JiraConfig` — `token` ← `APP__JIRA__TOKEN`. Дефолт
  `<PASSWORD>` (sentinel; якщо не перевизначити в `.env` — реальний токен
  буде literal `<PASSWORD>` і всі запити повернуть 401).
- `Settings.current_user: str` (`:53`) — Jira `key` поточного користувача
  (наприклад, `vstavitsky`). Дефолт `''`. Використовується в:
  - `UpdateJiraTask.update_worklog` — як `worker` для пошуку worklog-ів у Tempo.
  - `WorllogSyncTask.create_worklogs` — як `worker` при POST у Tempo.

Прапор `is_watched` у `jr_projects` — локальний фільтр, чи тягнути
issue/worklog цього проекту в синк. Виставляється вручну в БД.

---

## 10. Quirks / тех-борги

### Iменування

- **`is_archved`** (`jr_projects.is_archved`, `JiraProjectDTO.is_archved`,
  `JRProject.is_archved`) — typo, що пробралась через усі шари. Реальне
  Jira-поле — `archived`, мапиться правильно (`get_projects`, `:19`).
  Виправлення тягне: модель + DTO + alembic-ревізію + рефакторинг
  викликів.
- **`jr_worklogs.jr_issues_id`** — ім'я з зайвою `s`. Решта таблиць —
  однина (`jr_project_id`, `tc_project_id`). Тягне рефакторинг моделі,
  DAO, alembic-ревізії.
- **`WorllogSyncTask`** (типо `Worllog` із двома `l`) — клас, файл
  (`worllog_sync_task.py`), імпорти. Таблиця в БД при цьому коректно
  називається `worklog_sync_tasks`. Перейменування обережне — багато
  імпортів.
- **`JiraService.serch_worklogs_by_user`** — typo (`serch` замість
  `search`). Public-метод, заміна — компатибільність.

### Логіка / надійність

- **Copy-paste bug у `search_issues`** (`src/services/jira/jira_service.py:51, 61`):
  ```python
  reporter_field: dict = fields.get('reporter')
  if project_field is not None:        # ← має бути reporter_field
      reporter = JiraUserDTO(...)
  ```
  Те саме на `creator` (`:51`). Наслідки:
  - Якщо в issue нема `project` — `creator`/`reporter` теж не побудуються, навіть якщо їхні поля є.
  - Якщо `project` є, але `creator_field`/`reporter_field` — `None`, код **впаде** (NPE при `.get(...)`).
- **Жодної пагінації у `search_issues`** — Jira `api/2/search` за дефолтом
  повертає до `maxResults=50`. Якщо передали >50 ключів, тихо
  втрачаємо хвіст. Не вказано ні `startAt`, ні `maxResults`, ні явне
  `fields=...` (тягнеться весь default-набір — повільно).
- **JQL без екранування** (`:24`): `'key in ({})'.format(','.join(keys))`.
  Якщо `keys` містить дивні символи — рядок зламається. Поточні keys —
  безпечні (`[A-Z]+-\d+`), але input-валідації нема.
- **`create_worklog` приймає, що відповідь — непорожній список**
  (`:145: dict(worklogs[0])`). Якщо Tempo поверне `[]` чи `{}` —
  `IndexError`/`KeyError`.
- **`_make_request` повертає `{}` при помилці** — це маскує мережеві
  збої у `search_issues`/`serch_worklogs_by_user` (бачать як «порожньо»),
  але **не** маскує у `create_worklog` (там валиться при індексації).
  Поведінка неконсистентна.
- **Тип-анотація `_make_request -> dict`** не відповідає реальності для
  search-endpoint-ів (повертають `list`).

### Архітектурні нюанси

- **`UpdateJiraTask.update_worklog`** після імпорту worklog-ів тригерить
  `update_jira_issues(<keys>)` для оновлення issue-метаданих. Це створює
  додаткові HTTP-виклики на кожен прогон імпорту.
- **`WorllogSyncTask.create_worklogs` коммітить після кожного
  worklog-а** (`:80`). Якщо мережа падає посеред пачки — частина задач
  у `created`, частина в `create`. Це фіча (idempotent re-run), не баг.
- **`current_user` — глобальний з settings.** Імпорт worklog-ів і POST
  у Tempo завжди йдуть від імені цього юзера. Багатокористувацький
  сценарій вимагав би refactor усіх тасків (передавати worker
  параметром).
- **Кеш `SyncTaskService` (TC) тримає Jira-ключі** з `JRProjectDAO.all_keys_sync`,
  TTL 2 год. Якщо додати новий Jira-проект — entries TimeCamp для нього
  до 2 год можуть не визначити issue_key (`integrations/timecamp.md` §7).
