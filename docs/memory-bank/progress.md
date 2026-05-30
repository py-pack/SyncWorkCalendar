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

- [`add-rest-api`](../../openspec/changes/add-rest-api/) — FastAPI REST API
  імплементовано (2026-05-13): auth (single-user JWT з multi-user-ready
  схемою `api_users`), `api_jobs` із кроком `needs_verification`,
  read-endpoint-и стану синхронізації, sync-triggers навколо існуючих
  тасків, PATCH для `tc_projects.is_sync`/`issue_key`. Залишилось:
  ручний QA через Swagger UI (фаза 11 у `tasks.md`), архівація через
  `/openspec-archive-change`. Тех-довідка — `docs/technical/api-reference.md`.

## Що працює (HTTP API)

- FastAPI app (`src/api/app.py`) із CORS і глобальними exception handler-ами.
- JWT auth (`/auth/login`, `/auth/refresh`, `/auth/me`) поверх `api_users`.
- `api_jobs` lifecycle (`running → needs_verification → verified`, або
  `running → failed`) — wrapper `src/api/jobs_wrapper.run_job`.
- Read-endpoints: `/tc-projects` (з `entries_count`), `/jr-projects` (з
  `issues_count`), `/worklog-sync-tasks` (із summary), `/tc-entries/untracked`.
- PATCH `/tc-projects/{id}` з `extra=forbid` і регексом для `issue_key`.
- 8 sync-trigger endpoint-ів з опційним `?background=true`.

## Що не реалізовано

- Сценарій оновлення (`pre_update → update → updated`) — статуси оголошені,
  логіки немає.
- Видалення раніше створених worklog-ів у `Tempo`.
- Тести (юніт/інтеграційні) і CI.
- Управління користувачами через API/CLI — закривається через окрему
  майбутню зміну `add-user-management-cli`. Зараз — ручний INSERT (інструкція
  в `api-reference.md`).
- TTL/cron для старих `api_jobs` — `add-api-jobs-cleanup`.
- RBAC, per-user OAuth-токени на Jira/TimeCamp — окремі майбутні зміни.

## Поточний стан гілки

- Branch: `main`.
- Незакомічене: `M main.ipynb` (зміна періоду на 2026-04-08…2026-04-13)
  плюс імпементація `add-rest-api` (нові файли `src/api/`, `src/models/api_*.py`,
  `src/dao/api_*_dao.py`, `run_api.py`, alembic-ревізія `ef2c7288bbb0`).
- Остання міграція: `ef2c7288bbb0` (2026-05-13, `add_api_layer_tables`).
- Алембік head відповідає поточним моделям після застосування ревізії.

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
