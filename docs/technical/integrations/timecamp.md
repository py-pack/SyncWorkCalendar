# Інтеграція з TimeCamp

Технічна довідка по інтеграції з `TimeCamp` станом на 2026-05-11. Описує
HTTP-клієнт, DTO, ORM-моделі, DAO-операції, парсинг опису та повну схему
таблиць БД.

## 1. Огляд

`TimeCamp` — зовнішнє SaaS-джерело таймер-записів. Інтеграція **тільки на
читання**: проект тягне `projects` і `entries` за період, нормалізує дані та
кладе в локальні таблиці `tc_projects`, `tc_entries`. Жодних записів назад у
`TimeCamp` не відбувається.

Сутність `TCEntry` далі бере участь у конвеєрі `TimeCamp → Tempo Worklog`
(див. `../../memory-bank/systemPatterns.md` і `../../memory-bank/decisinLog.md` D-006).

## 2. Зовнішнє API

**Base URL:** `https://app.timecamp.com/third_party/api/`
**Auth:** заголовок `Authorization: Bearer <APP__TC__TOKEN>`
**Формат:** до кожного запиту додається `params['format'] = 'json'`.

| Метод | Endpoint  | Параметри                            | Призначення                                  |
| ----- | --------- | ------------------------------------ | -------------------------------------------- |
| GET   | `tasks`   | —                                    | Список проектів/задач (плоский словник)      |
| GET   | `entries` | `from=YYYY-MM-DD HH:MM:SS`, `to=...` | Таймер-записи за період (від 00:00 до 23:59) |

Запити інкапсульовані в `TCRequestService._make_request` (`src/services/time_camp/tc_request_service.py:62`).
Помилки `requests.RequestException` поглинаються — повертається `{}` і друкується в stdout.

## 3. DTO (Pydantic v2)

`src/services/time_camp/dto.py`:

```text
TCProjectDTO  — id, name, parent_id, user_id, level, is_archived,
                color, created_at, updated_at
TCTaskDTO     — id, tc_project_id, description, start_at, end_at, updated_at
```

Обидва DTO мають `field_validator('id', mode='before')`, який приводить ID
до `int` і повертає `None` для значень `≤ 0`. `Config.from_attributes = True` —
дозволяє створювати DTO з ORM-моделей.

Маппінг з відповіді API:

- `tasks`: словник з ключами `task_id → {name, parent_id, assigned_by, level, archived, color, add_date, modify_time}` (див. `TCRequestService.get_projects`, рядки 14-32).
- `entries`: список об'єктів з полями `id, task_id, description, date, start_time, end_time, last_modify`. `start_at` і `end_at` склеюються як `f"{date} {start_time}"` / `f"{date} {end_time}"`.

## 4. Потік даних

```
TimeCampUpdateTask
   ├─ update_project()      → TCRequestService.get_projects → TCProjectDAO.sync_all
   └─ update_entries(start, end)
                            → TCRequestService.get_entries(from, to)
                            → TCEntriesDAO.sync_all_between(...)
```

- `TCProjectDAO.sync_all` — наслідує `BaseDAO`, робить **full-replace** усіх
  записів `tc_projects` за `id` (`../../memory-bank/decisinLog.md` D-005).
- `TCEntriesDAO.sync_all_between` — обмежує DELETE діапазоном `[from 00:00,
  to 23:59]` по `start_at`, щоб не зачепити записи за інші періоди.

Друга роль `TCEntriesDAO` — `get_entries_for_worklogs(date_from, date_to)`:
`LEFT JOIN` на `WorklogSyncTask` за `source_id`, фільтр `TCProject.is_sync = TRUE`
і `WorklogSyncTask.source_id IS NULL` — повертає `WorklogTaskDTO` для тих
entries, що ще не мають таску синхронізації.

## 5. ORM-моделі

`src/models/tc_project.py` — `TCProject`:

- `name: String UNIQUE NOT NULL`
- `parent_id: Integer NULL` (ієрархія TimeCamp)
- `user_id: Integer NULL` (assigned_by з API)
- `level: SmallInteger DEFAULT 1`
- `is_archived: Boolean DEFAULT FALSE`
- `is_sync: Boolean DEFAULT FALSE` — **локальний прапор**, керує тим, чи
  потрапляють entries цього проекту в worklog-конвеєр. Виставляється вручну.
- `issue_key: String NULL` — fallback `Jira` key, якщо в описі entry ключ
  не знайдено.
- `color: String NULL`
- `created_at`, `updated_at: TIMESTAMPTZ`
- `relationship ts_entries → TCEntry` (через явний `primaryjoin` із `foreign()`,
  бо у схемі немає FK constraint).

`src/models/tc_entry.py` — `TCEntry` (`__tablename__ = 'tc_entries'`):

- `tc_project_id: Integer NULL` — м'який зв'язок із `TCProject.id`, без FK.
- `description: String NULL`
- `meta: JSON NULL` — оновлюється `event.listen('set', description)` (див. §7).
- `start_at: DateTime NOT NULL` (БЕЗ timezone)
- `end_at: DateTime NOT NULL` (БЕЗ timezone)
- `duration: Integer GENERATED` — `Computed("EXTRACT(EPOCH FROM end_at - start_at)")`,
  кількість секунд. Не передається з коду — обчислюється Postgres-ом.
- `updated_at: TIMESTAMPTZ DEFAULT now()`.

## 6. DAO-шар

`src/dao/tc_project_dao.py` — `TCProjectDAO`:

- Наслідує `BaseDAO`, моделює тільки `model = TCProject`. Жодних додаткових
  методів.

`src/dao/tc_entries_dao.py` — `TCEntriesDAO`:

- `sync_all_between(db, entries, date_from, date_to)` — період-обмежений
  full-replace.
- `get_entries_for_worklogs(db, date_from, date_to) → list[WorklogTaskDTO]` —
  SELECT з JOIN `TCProject`/`WorklogSyncTask`, фільтр `is_sync=True` і
  відсутність відповідного `worklog_sync_task`.
- `_create_content_by_template(content, key, start, end)` — будує рядок
  `sync|HH:MM|HH:MM - <content>` для подальшого виклику Tempo (формат, який
  `JRWorklog.change_to_description` потім ре-парсить у `meta`).
- `WorklogTaskDTO` — допоміжний Pydantic-контейнер `(status, source_id,
  worker_key, issue_key, content, started_at, time_spent)`.

## 7. Парсинг `description` → `meta.task`

`tc_entry.change_tc_entry_description` (event listener `'set'` на колонці
`description`):

1. При зміні значення викликає `SyncTaskService.match_task(value)`.
2. Якщо знайдено `task_key` — кладе у `target.meta['task']` і `flag_modified`.
3. Якщо ні — `target.meta = None`.

`SyncTaskService` (`src/core/utils/sync_task_service.py`):

- Регулярка `(?P<project_key>[A-Za-z]{2,8})-(?P<task_num>\d{1,4})` — пряме
  співпадіння ключа `Jira` у тексті, фільтрується списком ключів `JRProject`.
- Інакше — пробігає по шаблонах із таблиці `key_templates` (regex, якщо текст
  обгорнуто `/.../`, інакше — escaped substring case-insensitive, див.
  `convert_str_to_regex` у `src/utils/case_converter.py`).
- Кеш: класові атрибути `project_key`, `project_templates`, TTL 2 години
  (`D-003`). Кеш заповнюється **синхронним** SQLAlchemy session-ом
  (`JRProjectDAO.all_keys_sync`), бо event-listener не може робити `await`.

Якщо у `entry.meta['task']` нічого нема, fallback — `TCProject.issue_key`
з пов'язаного проекту (`TCEntriesDAO.get_entries_for_worklogs`, рядки 72-76).

## 8. Налаштування

- `.env` → `APP__TC__TOKEN` — обов'язковий токен TimeCamp.
- `tc_projects.is_sync` — вручну виставляється в `TRUE` для тих проектів, чиї
  entries мають потрапляти у worklog-конвеєр. За замовчуванням `FALSE`.
- `tc_projects.issue_key` — необов'язково; використовується як fallback ключ,
  якщо опис entry не містить ні ключа, ні шаблону.

## 9. Схема таблиць (DDL)

Реальні DDL з міграцій `a8cf9e93c99e`, `82f082ce0b72`:

```sql
CREATE TABLE tc_projects (
    id           INTEGER       PRIMARY KEY,
    name         VARCHAR       NOT NULL UNIQUE,
    parent_id    INTEGER       NULL,
    user_id      INTEGER       NULL,
    level        SMALLINT      NOT NULL DEFAULT 1,
    is_archived  BOOLEAN       NOT NULL DEFAULT FALSE,
    is_sync      BOOLEAN       NOT NULL DEFAULT FALSE,
    issue_key    VARCHAR       NULL,
    color        VARCHAR       NULL,
    created_at   TIMESTAMPTZ   NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ   NULL DEFAULT now()
);

CREATE TABLE tc_entries (
    id              INTEGER     PRIMARY KEY,
    tc_project_id   INTEGER     NULL,                  -- м'який зв'язок із tc_projects.id
    description     VARCHAR     NULL,
    meta            JSON        NULL,                  -- {"task": "<JIRA-KEY>"}
    start_at        TIMESTAMP   NOT NULL,              -- без timezone
    end_at          TIMESTAMP   NOT NULL,              -- без timezone
    duration        INTEGER     GENERATED ALWAYS AS    -- секунд між start_at і end_at
                    (EXTRACT(EPOCH FROM end_at - start_at)) STORED NOT NULL,
    updated_at      TIMESTAMPTZ NULL DEFAULT now()
);
```

Допоміжна таблиця для парсингу опису (міграція `5f712ea0757b`):

```sql
CREATE TABLE key_templates (
    id         INTEGER  PRIMARY KEY,
    issue_key  VARCHAR  NOT NULL,         -- цільовий ключ Jira
    template   VARCHAR  NOT NULL          -- escaped substring або /regex/
);
```

Зв'язки і обмеження:

- FK не оголошені — `tc_entries.tc_project_id → tc_projects.id` тримається
  тільки логікою застосунку (`relationship(..., primaryjoin=..., foreign(...))`).
- Унікальність `tc_projects.name` — це обмеження приходить з API TimeCamp,
  де ім'я задачі унікальне в межах акаунту.

## 10. Тех-борги та обмеження

- **Немає FK на `tc_project_id`.** При видаленні `TCProject` запис entry
  залишається з висячим `tc_project_id`.
- **`start_at`/`end_at` без timezone.** Постгрес зберігає як локальне; для
  обчислення `duration` це працює, але порівняння з `TIMESTAMPTZ` (наприклад,
  `worklog_sync_tasks.started_at`) — неявний каст.
- **`TCRequestService.get_entries`** обмежує `to` на `time.max` (23:59:59.999999) —
  записи, що почалися рівно опівночі наступного дня, не потрапляють.
- **TimeCamp API повертає словник, а не список** у `tasks` — `get_projects`
  ітерується по `.items()`. Якщо TimeCamp змінить формат — імпорт впаде.
- **`_make_request` повертає `{}` при будь-якій помилці** — caller отримує
  пустий словник, а не виключення. Це маскує мережеві збої.
- **Кеш `SyncTaskService` не інвалідовується явно** при оновленні
  `JRProject` чи `KeyTemplate` — TTL 2 год.
