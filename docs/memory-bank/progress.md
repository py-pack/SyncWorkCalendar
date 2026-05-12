# Progress

## Що працює

- Синхронізація проектів `TimeCamp` → таблиця `tc_projects` (включно з
  ієрархією, кольорами, архівним прапором).
- Синхронізація entries `TimeCamp` за період → `tc_entries` (з обчисленням
  `duration` через `Computed("EXTRACT(EPOCH FROM end_at - start_at)")`).
- Парсинг `description` entry на `meta.task` через `SyncTaskService` з кешем
  ключів проектів та regex-шаблонів.
- Синхронізація проектів `Jira` → `jr_projects`.
- Точкова синхронізація issue-ів `Jira` за ключами (`UpdateJiraTask.update_jira_issues`)
  + автозаповнення `jr_users` і `jr_projects` з фактів.
- Тягнення worklog-ів `Tempo` через `serch_worklogs_by_user` (typo у назві
  методу збережене для сумісності).
- Створення `WorklogSyncTask` (статус `pre_create`) для entries без пари
  у `worklog_sync_tasks`.
- Стадія `before_create` — підтягує відсутні `JRIssue` за ключами та
  переводить таски у `create`.
- `create_worklogs` — викликає `Tempo` POST `worklogs`, зберігає `target_id`
  і переводить таски в `created`.

## Що в роботі (OpenSpec)

- [`add-rest-api`](../../openspec/changes/add-rest-api/) — FastAPI REST API:
  auth (single-user JWT), read-endpoint-и стану синхронізації, sync-triggers
  навколо існуючих тасків, PATCH для `tc_projects.is_sync`/`issue_key`.
  Артефакти готові, очікує `/openspec-apply-change`.

## Що не реалізовано

- HTTP API на `FastAPI` — залежності встановлені, `src/api/` порожній.
  Закривається через `add-rest-api` (див. вище).
- Сценарій оновлення (`pre_update → update → updated`) — статуси оголошені,
  логіки немає.
- Видалення раніше створених worklog-ів у `Tempo`.
- Тести (юніт/інтеграційні) і CI.
- Робота кількох користувачів — `current_user` один на конфіг.

## Поточний стан гілки

- Branch: `main`.
- Незакомічене: `M main.ipynb` (зміна періоду на 2026-04-08…2026-04-13).
- Остання міграція: `b4117e0c3dd4` (2024-10-02).
- Алембік head відповідає поточним моделям — нових міграцій не потрібно
  (станом на 2026-05-11).

## Відомі тех-борги

- Typo `worllog_sync_task.py` / `WorllogSyncTask` — не виправлено через
  ризик зачепити імпорти.
- `DatabaseHelper` у `core/db_helper.py` помічений як `deprecated`, але не
  видалений.
- `BaseDAO._sync` видаляє моделі, відсутні у вхідному DTO — для повних дампів
  безпечно, для часткових — небезпечно (використовуйте `update_by_keys` або
  `sync_all_between`).
- `JiraService.search_issues` — у блоках `creator`/`reporter` перевіряється
  `if project_field is not None` замість відповідних `*_field` (баг).

Деталі рішень — у `decisinLog.md`.
