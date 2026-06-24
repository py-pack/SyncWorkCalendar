## Why

Екран `/jira` зараз показує задачі (`GET /jr-issues`) майже «як є»: без пагінації
(тягне лише перші 50 рядків), без фільтрів і **з авто-синком при відкритті** —
`autoSyncIssues` у фоні робить re-sync **усіх** відомих ключів задач, що
користувач визнав некоректним патерном (зайве навантаження на зовнішнє API + шум
`api_jobs`). Задач багато, вони створювались роками, тож без пагінації й фільтрів
екран некерований. Потрібен повноцінний екран задач Jira з вибором періоду
створення, фільтрами (проект / статус / пошук за назвою), пагінацією та **явною**
кнопкою синку — за тим самим принципом, що вже застосовано до `/timecamp`
(`rework-timecamp-entries-screen`).

## What Changes

- **BREAKING (поведінка екрана):** `/jira` більше **не** робить авто-синк при
  відкритті. Екран читає **лише з локальної БД**; синхронізація з Jira — тільки
  через явну кнопку. Авто-синк (`autoSyncIssues` на `onMounted`) прибирається з
  екрана.
- **BREAKING (контракт `GET /jr-issues`):** відповідь стає сторінкованою
  `{ items, total }` (дзеркало `TCEntriesResponse`) замість плоского списку.
  Додаються параметри:
  - `status` — точний фільтр за статусом задачі (опційний);
  - `created_from` / `created_to` — фільтр за `jr_issues.created_at`; дефолт —
    **поточний місяць** (через `_current_month`, як на `/timecamp`);
  - `offset` (дефолт `0`); `limit` лишається, але дефолт `50`, кап `200`.
  - `project_id` і `q` (ILIKE по `key`/`name`) — лишаються.
  - Сортування — за `created_at` спадно (`NULL` останніми).
  - `total` — кількість за тим самим фільтром без `limit`/`offset`.
  - Єдиний інший споживач (`jrIssueSearch` у select-і мапінгу TimeCamp-проектів)
    переводиться на читання `.items` — зміна локальна.
- **Новий facet-ендпоінт `GET /jr-issues/statuses`** — перелік **усіх наявних у
  БД** статусів для наповнення випадайки фільтра статусу.
- **Переписаний екран `/jira`**: тулбар із фільтрами (випадайка проекту, випадайка
  статусу, пошук за назвою, контрол періоду створення), серверна пагінація,
  кнопка синку у правому верхньому куті. Порядок колонок — **проект → тип →
  статус → номер (ключ) → опис**.
- **Попап синку** з вибором періоду та швидкими шаблонами, що відтворює потік із
  ноутбука (`api/main.ipynb`, рядки 25–31): `update_all_projects()` +
  `update_worklog(start, finish)` — тобто послідовно `POST /sync/jira/projects`
  і `POST /sync/jira/worklogs` за обраний період. Задачі підтягуються як побічний
  ефект синку worklog-ів (`update_worklog` → `update_jira_issues`).

## Capabilities

### New Capabilities
<!-- Нових capability ця зміна не вводить — лише модифікує наявні. -->

### Modified Capabilities

- `api-jira-read`: вимога «Список Jira-задач» переписується — `GET /jr-issues`
  стає сторінкованим (`{ items, total }`, `offset`/`limit`) із додатковими
  фільтрами `status` і `created_from`/`created_to` (дефолт — поточний місяць),
  сортуванням за `created_at` спадно; додається нова вимога «Перелік статусів
  Jira-задач» (`GET /jr-issues/statuses`). Вимога про `PATCH /jr-projects/{id}`
  лишається без змін.
- `frontend-data-tables`: вимога «Екран Jira» переписується — замість показу всіх
  задач + авто-синк екран читає з локальної БД за обраним періодом створення з
  пагінацією, фільтрами (проект / статус / пошук за назвою), новим порядком
  колонок (проект → тип → статус → номер → опис) і явною кнопкою синку з попапом
  (період + шаблони). Авто-синк прибрано.

## Impact

- **Backend (`api/`):** `app/api/routers/jr_issues.py` (пагінація + фільтри
  `status`/`created_from`/`created_to` + новий handler `GET /jr-issues/statuses`);
  `app/api/schemas/jr_issues.py` (обгортка `JRIssuesPage { items, total }`,
  `JRIssueItem` без змін полів); `app/dao/jr_issues_dao.py` (`list_paginated` з
  фільтрами + окремий `COUNT`; `distinct_statuses`). Хелпери `_current_month` /
  `_period_or_400` переюзовуються (за потреби виносяться зі `routers/sync_status.py`
  у спільне місце). **Без alembic-міграції** (колонка `created_at` уже існує; head
  `10b7dc50b00f`).
- **Frontend (`front/`):** `views/JiraView.vue` (переписаний на `DataPage` +
  тулбар фільтрів + пагінація + попап синку; `onMounted` — лише `loadJrIssues`,
  без авто-синку); новий `components/jira/SyncIssuesModal.vue` (за патерном
  `components/timecamp/SyncEntriesModal.vue`); невеликий переюзовний `Select`/
  dropdown (проект + статус) на патерні поповера `components/ui/Menu.vue` (без
  зовнішньої бібліотеки; вибір проекту — з пошуком, як select задачі у
  `SyncSettingsModal.vue`); `stores/tables.ts` (стан екрана Jira:
  `jrPeriod`/`jrStatus`/`jrProjectFilter`/`jrQuery`/`jrOffset`/`jrTotal`/
  `jrPageSize` + `loadJrIssues` + сетери + `syncJrIssues(period)`; прибрати виклик
  `autoSyncIssues` з екрана); `api/client.ts` (`jrIssues` → `JRIssuesPage` з новими
  параметрами; новий `jrIssueStatuses`; новий `syncJrWorklogs(period)`; `syncJrProjects`
  лишається); `api/types.ts` (`JRIssuesPage`); виправити `jrIssueSearch` на читання
  `.items`; i18n (UK+EN) — переюз `col_project`/`col_type`/`col_status`/`col_key`/
  `col_desc`, `period_*`, `page_prev`/`page_next`, нові ключі під фільтри й попап.
- **Out of scope:** ручне зіставлення untracked-записів із задачами; редагування
  задач і round-trip у Tempo; перенесення цього ж патерну на `/tempo` —
  **наступна окрема зміна**. Жодних змін схеми БД / alembic.
