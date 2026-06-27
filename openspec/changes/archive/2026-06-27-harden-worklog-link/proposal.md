## Why

Звʼязок TimeCamp↔Tempo тримається на **неявному** матчингу: `worklog_sync_tasks`
(WST) уже містить місток `source_id` (= `tc_entries.id`) і `target_id`
(= `jr_worklogs.id`), але обидві — звичайні `Integer`-колонки **без FK і без
`UNIQUE`**, а дедуп (`JRWorklogDAO.find_match`) щоразу **переоб'являє** збіг
кортежем `(issue, worker, started_at, duration)` замість того, щоб довіряти лінку.
Наслідки: `target_id` може дангліти на видалений worklog; один tc-запис може мати
кілька WST; орфан-дублі в Tempo (worklog без WST) непомітні структурно. Це
першопричина того, що дублі взагалі стали можливі й невидимі. Потрібен **явний,
забезпечений констрейнтами** місток, якому довіряє дедуп.

## What Changes

- **`UNIQUE(source_id)` на `worklog_sync_tasks`:** один місток на один TimeCamp-запис
  (структурно унеможливлює дубль-WST; сьогодні це лише припущення upsert-логіки).
- **FK `worklog_sync_tasks.target_id → jr_worklogs.id` з `ON DELETE SET NULL`:**
  коли worklog зникає з Tempo (видалення / чистка дублів) — лінк автоматично
  занулюється, без дангл-посилань. (Узгоджено з чисткою дублів
  `add-worklog-dedup-cleanup`: занулення замість «битого» лінку.)
- **На `source_id` — лише `UNIQUE`, без hard-FK** (рішення користувача): TimeCamp і
  Tempo — різні сервіси, синхронимо за можливості, а локальну історію WST **не
  чіпаємо** автоматично (крім некоректної — задвоєння). `UNIQUE` тримає кардинальність
  містка; посилання на `tc_entries` лишається на app-рівні. (Жодного `CASCADE` — він
  стирав би історію; це ще й прибирає головний ризик взаємодії з re-sync.)
- **Дедуп довіряє явному лінку:** `target_id` (де він є) — канонічне джерело правди
  «цей worklog уже представлено»; матчинг кортежу лишається **fallback** для орфанів
  і worklog-ів, створених поза конвеєром.
- **Міграція спершу нормалізує наявні дані** (дедуп WST за `source_id`, занулення
  дангл-`target_id`), щоб констрейнти можна було накласти без помилок. Видаляються
  **лише** задвоєні WST (некоректна історія), осиротілі за `source_id` — лишаються.
- **BREAKING (схема):** alembic-ревізія поверх head `69dde0d17ff2`.

## Capabilities

### New Capabilities

- `worklog-link-integrity`: явний місток TimeCamp↔Tempo як інваріант БД —
  `UNIQUE(source_id)` і FK `target_id → jr_worklogs` (SET NULL), **без** FK на
  `source_id` (історію не чіпаємо), плюс одноразова нормалізація наявних даних
  (чистка задвоєних WST + дангл-`target_id`) перед накладанням констрейнтів.

### Modified Capabilities

- `backend-auto-linking`: вимога **Дедуп проти наявних Tempo-worklog-ів**
  переписується так, щоб дедуп **спершу довіряв** явному лінку `WST.target_id`
  (канонічне «вже представлено»), а кортеж `(issue, worker, started_at, duration)`
  використовував лише як **fallback** для незв'язаних/орфанних worklog-ів.

## Impact

- **Backend / схема:** нова alembic-ревізія (head → новий) із (1) data-fix
  (`DELETE` задвоєних WST за `source_id`, `UPDATE target_id=NULL` для дангл),
  (2) `CREATE UNIQUE` на `source_id`, (3) `ADD FOREIGN KEY` лише на `target_id`
  (`SET NULL`). Моделі `app/models/worklog_sync_task.py` (декларація `unique` +
  target-FK). DAO/таски: `JRWorklogDAO.find_match` і виклики в
  `ReconcileLinksTask._push`/`WorllogSyncTask.push_one` — «лінк → fallback кортеж».
- **Взаємодія з дзеркалами:** `jr_worklogs` — зовнішнє дзеркало, що **видаляє** рядки
  на повторному синку (`sync_all_between`). Перевірити, що FK `target_id`
  (`SET NULL`) коректно взаємодіє з re-sync (зниклий у пулі worklog — легітимно
  видалений, занулення коректне; status-гард не дає ре-пушу). На `source_id` FK немає,
  тож re-sync `tc_entries` не зачіпається взагалі. Деталі — `design.md`.
- **Послідовність:** мерджити **після** `harden-job-retry` і **перед**
  `add-worklog-dedup-cleanup` (чистка дублів спирається на надійний `target_id` і
  `ON DELETE SET NULL`).
