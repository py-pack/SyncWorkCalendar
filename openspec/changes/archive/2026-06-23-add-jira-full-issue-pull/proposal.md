## Why

Локальна таблиця `jr_issues` наповнюється **лише як побічний ефект синку
worklog-ів**: `UpdateJiraTask.update_worklog` бере ключі задач із Tempo-worklog-ів
періоду й тягне **тільки** ці ключі (`JiraService.search_issues` будує JQL
`key in (...)`). Тож задачі, на які користувач не логав час у Tempo — зокрема щойно
створені й «загальні»/не-заасайнені — у локальну БД **не потрапляють**. На QA
екрана `/jira` (`rework-jira-issues-screen`) це й проявилось: за рік локально
видно лише десятки задач, хоча в Jira їх значно більше. Жодна зміна фільтра/періоду
цього не виправить — потрібен **повний витяг** задач відстежуваних проектів.

## What Changes

- **Новий бекенд-потік повного витягу задач:** пошук у Jira за JQL
  `project IN (KEY, …)` (а не лише `key in (…)`) **з пагінацією** (цикл
  `startAt`/`maxResults` поки не вибрано все) — на відміну від наявного
  `search_issues`, який **не** пагінує (кап ~50 за виклик). Витягуються **усі**
  задачі проекту, **без** фільтра за `worker_key`/assignee/reporter (включно з
  чужими).
- **Скоуп — лише відстежувані проекти** (`jr_projects.is_watched = true`): новий
  метод `UpdateJiraTask` читає watched-проекти з БД і тягне всі їхні задачі;
  upsert у `jr_issues` через наявний `JRIssuesDAO.sync_by_key`/`update_by_keys`
  (**не** full-replace — щоб не видаляти задачі поза вибіркою).
- **Новий sync-trigger endpoint** `POST /sync/jira/issues-all` у стилі наявних у
  `routers/sync_triggers.py` (обгорнутий `run_job` → лог у `api_jobs`; опційний
  `?background=true` → `202` + поллінг, бо повний витяг великого проекту може бути
  довгим).
- **Фікс латентного бага** в `JiraService.search_issues`: рядки перевірки
  `creator`/`reporter` помилково дивляться на `project_field` замість
  `creator_field`/`reporter_field` (тех-борг із `progress.md`) — виправляється тут,
  бо новий потік переюзовує цей самий парсинг.
- **Фронтенд:** дія «повний витяг задач» на екрані `/jira` (додатковий пункт/кнопка
  поряд із наявним синком, напр. у `SyncIssuesModal`), із перезавантаженням списку
  після завершення.
- **Без зміни схеми БД** (`jr_issues` має всі потрібні колонки) — **без
  alembic-міграції**; head лишається `10b7dc50b00f`.

## Capabilities

### New Capabilities
<!-- Нових capability ця зміна не вводить — лише доповнює наявні. -->

### Modified Capabilities

- `api-sync-triggers`: **ADDED** вимога «Повний синк задач Jira за відстежуваними
  проектами» (`POST /sync/jira/issues-all`) — повний витяг усіх задач watched-
  проектів за JQL `project IN (…)` з пагінацією, обгорнутий `run_job`, опційний
  `background`. Наявні sync-тригери не змінюються.
- `frontend-data-tables`: **ADDED** вимога «Повний витяг задач Jira» — дія на екрані
  `/jira`, що запускає `POST /sync/jira/issues-all` і перезавантажує список.
  (Наявна вимога «Екран Jira» не змінюється — нова вимога додається поряд, щоб не
  конфліктувати з `rework-jira-issues-screen`.)

## Impact

- **Backend (`api/`):** `app/services/jira/jira_service.py` (новий пошук за JQL
  проектів із пагінацією + фікс `creator`/`reporter`); `app/tasks/jira_update_task.py`
  (новий `update_issues_for_watched_projects()` — читає `is_watched`-проекти,
  тягне всі їхні задачі, upsert через `JRIssuesDAO`); `app/api/routers/sync_triggers.py`
  (+`POST /sync/jira/issues-all`, `_do_jr_issues_all` у стилі наявних `_do_*`);
  без нових схем БД / alembic.
- **Frontend (`front/`):** `api/client.ts` (`syncJrIssuesAll()` →
  `POST /sync/jira/issues-all`); `stores/tables.ts` (дія повного витягу + reload
  `loadJrIssues`); `components/jira/SyncIssuesModal.vue` або `views/JiraView.vue`
  (контрол запуску); i18n (UK+EN).
- **Out of scope:** редагування задач і round-trip у Tempo; зміна екрана `/jira`
  (він уже читає з БД і підхопить нові рядки сам); синк за розкладом; повний витяг
  **не**-watched проектів. Жодних змін схеми БД / alembic.
