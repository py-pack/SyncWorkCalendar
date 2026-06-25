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

- [`add-api-jobs-cleanup`](../../openspec/changes/add-api-jobs-cleanup/)
  — **PROPOSAL (2026-06-25; `validate --strict` OK, 4/4 артефакти).** Будується
  поверх `rework-journal-screen` (архівувати після неї). Зупиняє безмежне
  зростання `needs_verification`/`api_jobs` і додає масовий verify + UX. Передумова:
  від `verified` нічого не залежить (grep-перевірено) — успіхи осідають у
  `needs_verification` (306). **Рішення:** авто-verify за TTL (Celery-таска
  закриває `needs_verification` старші за `APP__CELERY__AUTO_VERIFY_DAYS`=7,
  `verified_by="system"`); TTL-видалення термінальних старших за
  `APP__CELERY__JOB_TTL_DAYS`=90 (`running`/`needs_verification` не чіпає); кнопку
  зверху замінено на «Підтвердити всі» (`POST /api-jobs/verify-all` за фільтрами);
  бейдж `nowrap` + зведення лічильників у тулбарі. **Backend:** `CeleryConfig`
  +TTL; DAO `verify_matching`/`auto_verify_older_than`/`delete_terminal_older_than`/
  `status_summary`; `summary` у `GET /api-jobs`; maintenance-таска
  `beat.cleanup_api_jobs` (**без** `api_jobs`-аудиту) у beat ~`02:00`. **Без
  alembic** (head `69dde0d17ff2`). Дельти: MODIFIED `api-jobs`/
  `frontend-sync-journal`, ADDED у `async-task-queue`. Деталі — `design.md` (D1–D7).

- [`rework-journal-screen`](../../openspec/changes/rework-journal-screen/)
  — **РЕАЛІЗОВАНО 2026-06-25 (14/15 — лишився лише 5.3 браузерний QA, на
  користувача; `validate --strict` OK; `npm run build` чисто; бекенд-фікс
  верифіковано наживо).** Полагоджено зламаний `/journal` (усі `GET/POST
  /api-jobs/**` → **500**) і приведено екран до спільного формату дані-екранів.
  **Корінь 500:** схема `APIJobSummary/Detail` оголошує `status: Literal[str]`, а
  ORM-поле `APIJob.status` — член enum; `model_validate(<ORM>)` (список/деталі/
  verify) не коерсить enum→`.value` проти `Literal` → `ValidationError` на кожному
  рядку. Виплило лише тепер, бо Celery наповнив `api_jobs` (306 рядків
  `needs_verification`). **Реалізація:** (backend) `@field_validator(mode="before")`
  на `status` у `schemas/api_jobs.py` → рядок (без нових ендпоінтів, без alembic,
  head `69dde0d17ff2`); наживо `GET /api-jobs`/навбейдж/`{id}`/фільтр тригер+період
  → усі **200**, `status` як рядок. (frontend) `apiJobs(start/end)` у клієнті;
  переписаний `stores/journal.ts` (`period`=`defaultReviewPeriod()`/`statusFilter`/
  `triggerFilter`/`offset`/`pageSize`; сетери скидають `offset`→0; `needsCount`/
  `open`/`close`/`verify` без зміни); `JournalView.vue` — `PeriodPicker` + 2
  `FilterSelect` (статус + статичний `SYNC_TRIGGERS`) замість `.cal__chips`,
  серверна пагінація (`.tcpage`), дати через новий `fmtDateTime` (`lib/format.ts`)
  у таблиці й бічній панелі; i18n `job_flt_status`/`job_flt_trigger`/
  `job_verified_at`. «Мова синку» (`SyncState`/`SyncFilter`) тут НЕ застосовується
  (статус job-а 4-становий). Дельти: MODIFIED `api-jobs`, `frontend-sync-journal`.
  Деталі — `design.md` (D1–D6). Лишилось: 5.3 браузерний QA + git-commit.

- [`add-profile-run-now-sync`](../../openspec/changes/archive/2026-06-25-add-profile-run-now-sync/)
  — **ЗААРХІВОВАНО 2026-06-25 (16/17 — лишився лише 6.3 браузерний QA, на
  користувача; `validate --strict` OK; `npm run build` чисто; дельту злито в
  `openspec/specs/frontend-profile/`, `validate --specs --strict` 24/24 OK).**
  Кнопка «Запустити зараз» напроти кожного з 5 тумблерів `sync_prefs` на закладці
  «Синхронізації» → спільний попап `RunSyncModal.vue` (`PeriodPicker`, дефолт «цей
  місяць») → негайний запуск відповідної sync-дії за період. **Фронтенд-онлі**:
  усі тригери вже канонічні в `api-sync-triggers` (нових ендпоінтів немає, без
  alembic, head `69dde0d17ff2`). Реалізація: новий `api.reconcileLinks` (єдиний
  відсутній метод клієнта); `components/profile/runActions.ts` (мапа `RUN_ACTIONS`
  по ключу `keyof SyncPrefs` — метадані + `run(period)`, що кличе `api.*` напряму
  **без** релоаду інших екранів, D5; TimeCamp/Jira дзеркалять крон — проекти, далі
  дані, D3); `components/profile/RunSyncModal.vue` (дві гілки — синхронна дельта /
  `202 queued`→Журнал, D1/D2; `ApiError.detail` без закриття); кнопка `bolt`
  «Запустити зараз» у кожному `.sprefs__row` (рядок `<label>`→`<div>`), дизейбл
  worker_key-залежних дій без `worker_key` (D6); i18n `sp_run_now`/`rsync_*`
  (UK+EN); CSS `.sprefs__ctl`/`.rsync__*`. Дельта (злита в `openspec/specs/`) —
  MODIFIED `frontend-profile`. Лишилось — 6.3 браузерний QA (на користувача) +
  git-commit. Деталі — `design.md` (D1–D7) у теці архіву.

- [`add-celery-auto-linking`](../../openspec/changes/archive/2026-06-25-add-celery-auto-linking/)
  — **ЗААРХІВОВАНО 2026-06-25 (32/32; `validate --strict` OK; бекенд-верифікація
  наживо PASS). Дельти злиті в `openspec/specs/`: нові
  `async-task-queue`/`backend-auto-linking`; MODIFIED `container-orchestration`/
  `api-sync-triggers`/`api-users-management`/`api-auth` (`sync_prefs` у `/auth/me`).**
  Backend/інфра: `Celery 5.6`+`Redis`+`beat` у
  нових контейнерах `redis`/`worker`/`beat` (redis named volume, host-порт
  **`11332`**; worker `--pool=prefork --max-tasks-per-child=100`). Async→Celery
  місток `app/tasks/celery_bridge.py` (свіжий engine/loop на таску + спільне ядро
  `api_jobs`-аудиту з `jobs_wrapper`: `create_job`/`run_existing_job`). 8 тасок +
  2 beat-диспетчери (`app/tasks/celery_tasks.py`); beat `01:00` TimeCamp+Jira /
  `01:30` Tempo (`app/celery_app.py`; таймзона `APP__CELERY__TIMEZONE`, дефолт
  `UTC`), диспетчери поважають per-user `sync_prefs`. Авто-реконсиляція
  (`ReconcileLinksTask`): upsert WST за `source_id` (`TCEntriesDAO.
  get_match_candidates`), перелінк на зміну опису **без** авто-відлінку, дедуп
  `JRWorklogDAO.find_match`, **активований** `created→pre_update→update→updated`
  через `JiraService.update_worklog` (Tempo `PUT`); пуш гейтиться `auto_push_tempo`.
  Per-user `api_users.sync_prefs` (JSONB nullable, дефолт `NULL`→`false`, opt-in;
  хелпер `app/core/utils/sync_prefs.py`) + **alembic head `69dde0d17ff2`**
  (застосовано). API: `sync_prefs` у `GET /auth/me`, `PATCH /users/me/sync-prefs`
  (extra=forbid→422), `POST /sync/reconcile-links` (enqueue, 400 без `worker_key`),
  важкі тригери `?background=true` → enqueue (а не `BackgroundTasks`). 2 нові
  capability `async-task-queue`/`backend-auto-linking`; MODIFIED
  `container-orchestration`/`api-sync-triggers`/`api-users-management`/`api-auth`.
  Фронт-перемикачі `sync_prefs` доставила зміна 2 `rework-tempo-screen`. Лишилось:
  git-commit. Деталі — `design.md` (у теці архіву) + `activeContext.md`.
- [`rework-tempo-screen`](../../openspec/changes/archive/2026-06-25-rework-tempo-screen/)
  — **ЗААРХІВОВАНО 2026-06-25 (25/26 — лишився лише 6.3 браузерний QA; `validate
  --strict` OK; `npm run build` чисто; backend smoke 24/24 наживо PASS). Дельти злиті
  в `openspec/specs/`: новий `frontend-profile`; MODIFIED `frontend-data-tables`/
  `api-sync-status`/`api-sync-triggers`/`api-users-management`/`api-auth`/
  `web-app-shell`.**
  Екран `/tempo` під патерн `DataPage`: дві вкладені вкладки (`/tempo/worklogs` —
  `jr_worklogs`, `/tempo/pipeline` — WST-конвеєр), `PeriodPicker`+`SyncFilter`+
  **пошук за назвою**+пагінація, рядок показує номер **і назву** задачі (`issue_name`),
  пер-рядкова дія замість чекбоксів (`POST /sync/worklog-tasks/{id}/push`), кнопка
  «Забрати з Tempo» (попап `PullWorklogsModal`). Новий read `GET /jr-worklogs`
  (`JRWorklogDAO.list_with_link_state`, `is_linked` через EXISTS) + розширення `GET
  /worklog-sync-tasks` (пагінація/`total`/`synced`/`q`/`issue_name`). Per-id
  `WorllogSyncTask.push_one` (резолв issue → дедуп → Tempo create). Меню user-chip —
  **один** пункт «Профіль» → `views/ProfileView.vue` на двох закладках (self-edit
  `PATCH /users/me` крім `email`/`is_active`→422; зміна/set пароля `PATCH
  /users/me/password`; тумблери `sync_prefs`, дефолт вимкнено). `GET /auth/me`
  додатково віддає `email`+`is_active` (read-only профілю). Без bulk-попапа конвеєра
  (пер-рядковий пуш заміняє, D4). Без міграції (head `69dde0d17ff2`). Новий
  `frontend-profile`; MODIFIED `frontend-data-tables`/`api-sync-status`/
  `api-sync-triggers`/`api-users-management`/`api-auth`/`web-app-shell`. Споживає
  `sync_prefs` зі зміни вище. Лишилось: 6.3 браузерний QA (на користувача) + git-commit.

- [`add-jira-full-issue-pull`](../../openspec/changes/archive/2026-06-23-add-jira-full-issue-pull/)
  — **заархівовано 2026-06-23 (16/16; браузерний QA підтверджено користувачем;
  `validate --strict` OK; `npm run build` чисто). 2 дельти (ADDED) злиті в
  `openspec/specs/`: `api-sync-triggers`, `frontend-data-tables`.**
  Наслідок QA `rework-jira-issues-screen`: `jr_issues` має лише задачі з
  Tempo-worklog-ів. Додає витяг задач відстежуваних проектів (`is_watched`) **за
  період активності** (`updated`): пошук за JQL `project in (…) AND updated >= … AND
  updated <= "… 23:59"` з пагінацією (новий `_search` + `search_issues_by_projects`;
  +фікс бага `creator`/`reporter` у `JiraService`), `JRProjectDAO.watched_keys`,
  `UpdateJiraTask.update_issues_for_watched_projects(updated_from, updated_to)`
  (upsert через `sync_by_key`), тригер `POST /sync/jira/issues-all` (опційний
  `PeriodBody`, run_job, опц. background), **єдина** кнопка-попап на `/jira`
  (`SyncIssuesModal` із `PeriodPicker`). Без фільтра за worker_key/assignee (тягнемо
  й чужі задачі). Без alembic. Рішення — `design.md` (D1–D7).

- [`rework-jira-issues-screen`](../../openspec/changes/archive/2026-06-23-rework-jira-issues-screen/)
  — **заархівовано 2026-06-23 (24/24; браузерний QA підтверджено користувачем;
  `validate --strict` OK; `npm run build` чисто). Дельти злиті в `openspec/specs/`:
  `api-jira-read` (MODIFIED «Список Jira-задач» + ADDED «Перелік статусів»),
  `frontend-data-tables` (MODIFIED «Екран Jira»).**
  Дзеркало `rework-timecamp-entries-screen` на екран `/jira` (задачі): читати лише
  з локальної БД, авто-синк (`autoSyncIssues`) прибрано, явна кнопка синку, фільтри
  (проект / статус / пошук за назвою) + фільтр за **періодом активності**
  (`updated_at` — пост-QA пивот із `created_at`; `PeriodPicker`, дефолт екрана
  поточний рік) + серверна пагінація. Порядок колонок — проект → тип → статус →
  номер (`key`) → опис. Синк (одна кнопка-попап) виконує **витяг задач за період**
  (`POST /sync/jira/issues-all`, зміна `add-jira-full-issue-pull`), а не
  projects+worklogs. **BREAKING** `GET /jr-issues` → сторінкований `{ items, total }`
  + `status`/`updated_from`/`updated_to`; новий facet `GET /jr-issues/statuses`. Без
  alembic (head `10b7dc50b00f`). На екрані `SyncState`/`SyncFilter` не застосовуються
  (немає бінарного стану синку). Backend: новий спільний `app/api/period.py`
  (`current_month`/`period_or_400`, винесено зі `sync_status.py`), `JRIssuesPage`,
  `JRIssuesDAO.list_paginated` (фільтр/сорт за `updated_at`) +`distinct_statuses`.
  Frontend: `JRIssuesPage`-тип, `jrIssues`/`jrIssueStatuses` у клієнті, стан+дії Jira
  у `tables.ts` (видалено `autoSyncIssues`/`loadIssues`), нові
  `components/data/FilterSelect.vue` + `components/jira/SyncIssuesModal.vue`,
  переписаний `JiraView` на `DataPage`, i18n, CSS. **Рішення користувача:**
  мапінг-select (`jrIssueSearch`) шукає серед усіх задач — широкий період
  (`2000-01-01…2999-12-31`); `NULL updated_at` не потрапляє. Рішення — `design.md`
  (D1–D9).

- [`rework-timecamp-entries-screen`](../../openspec/changes/archive/2026-06-23-rework-timecamp-entries-screen/)
  — **заархівовано 2026-06-23 (27/27; браузерний QA підтверджено користувачем).
  2 дельти злиті в `openspec/specs/` і канонічні: `api-sync-status` (ADDED
  `GET /tc-entries`), `frontend-data-tables` (MODIFIED «Екран TimeCamp» + ADDED
  «Єдине відображення стану синку»). `npm run build` чисто, backend live smoke +
  DAO-перевірка PASS, `validate --strict` OK.** Переробка екрана `/timecamp`:
  замість лише незіставлених
  записів (`GET /tc-entries/untracked`, захардкоджений фільтр + 6-міс період +
  авто-синк) — усі записи з локальної БД за обраний період, серверна пагінація,
  фільтр стану синку (`усі|синхронізовані|не синхронізовані`), **явна** кнопка
  синку з попапом (період + шаблони). Рішення користувача: екрани читають **лише
  з БД**, синк **лише кнопкою** (без авто при відкритті) — патерн далі для `/jira`
  і `/tempo`; «синхронізовано» — бінарно за наявністю worklog у Tempo
  (`worklog_sync_task` `created`/`updated`, scoped по `worker_key`).
  Backend (`routers/sync_status.py` + `TCEntriesDAO.list_with_sync_state` через
  EXISTS на WST + схеми `TCEntryItem`/`TCEntriesResponse`): новий `GET /tc-entries`
  (`synced` фільтр + `limit`/`offset`/`total` + `is_synced`), `untracked`
  незмінний; **без міграції** (head `10b7dc50b00f`). Frontend: `api/types.ts`+
  `client.ts` (`tcEntries`), `lib/period.ts` (спільний `PERIOD_PRESETS`),
  `stores/tables.ts` (стан+`loadTcEntries`/`syncTcEntries`, прибрано
  `autoSyncEntries`/`loadUntracked`), нова `components/timecamp/SyncEntriesModal.vue`,
  переписаний `TimeCampView` (`DataPage`+пагінація+попап), i18n, CSS. **UI-рефінмент
  за фідбеком (D9):** компактний `components/data/PeriodPicker.vue` (dropdown зі
  шаблонами всередину, без зовнішньої бібліотеки) переюзаний тулбаром і попапом;
  фільтр — наявний `Segmented` (усі контроли зліва); задача — окрема колонка.
  **Уніфікація «мови синку» (D10/D11):** порядок колонок Проект→Задача→Опис→Дата→
  Час→Стан; дата `дд.мм.рррр` (`fmtDate`); спільні `components/data/SyncState.vue`
  + `SyncFilter.vue` (канонічний `SyncTri`, англ. підписи) — **ідентично** на
  `/timecamp`+`/projects/timecamp`+`/projects/jira` (прибрано локальні стилі/опції;
  патерн → `systemPatterns.md` + auto-memory). MODIFIED: `api-sync-status`,
  `frontend-data-tables`. Деталі — `design.md` (D1–D11).

- [`rework-jira-projects-subview`](../../openspec/changes/archive/2026-06-13-rework-jira-projects-subview/)
  — **заархівовано 2026-06-14 (11/12; браузерний QA 5.2 — наживо; git-commit).
  Дельта злита в `openspec/specs/frontend-data-tables/` (MODIFIED «Екран
  «Проекти»» + ADDED «Попап налаштувань синку Jira-проекту»). `validate --strict`
  OK, `npm run build` чисто.**
  Дзеркало TimeCamp-рішень на під-вʼюху «Проекти → Jira» (фронтенд-онлі): фільтр
  за станом синку (`is_watched`, клієнтський) + швидкий локальний пошук
  (`key`/`name`) + попап редагування замість інлайн-тогла (**простіший: лише
  тогл `is_watched`, Save завжди дозволено**) + тьмяні архівні; `issues_count`
  рахує всі задачі. Без дерева/кольору/тега (Jira-проекти плоскі). Бекенд не
  чіпається. MODIFIED `frontend-data-tables`. Рішення — `design.md` (D1–D5).

- [`add-page-shell-template`](../../openspec/changes/archive/2026-06-13-add-page-shell-template/)
  — **заархівовано 2026-06-13 (12/13; браузерний QA 4.2 — наживо; git-commit).
  Нова capability `frontend-page-shell` (3 вимоги) злита в `openspec/specs/` і
  канонічна. `validate --strict` OK, `npm run build` чисто.** Винесено
  переюзовний каркас сторінки `components/data/DataPage.vue` (заголовок + дії у
  верхньому правому куті + **закладки/окремі під-сторінки** (router-agnostic) +
  опційний тулбар + банер помилки + тіло); 6 в'юх переведено на нього,
  `PageHeader.vue` видалено (0 споживачів). Фронтенд-онлі, без зміни
  поведінки/бекенду/CSS. `CalendarView` — поза скоупом (інший клас екрана).
  Рішення — `design.md` (D1–D7).

- [`rework-projects-screen`](../../openspec/changes/archive/2026-06-13-rework-projects-screen/)
  — **заархівовано 2026-06-13 (26/27; браузерний QA 11.2 — наживо; git-commit).
  3 capability-дельти злиті в `openspec/specs/` і канонічні: `api-jira-read`,
  `api-tc-projects-management`, `frontend-data-tables`. `validate --strict` OK,
  `npm run build` і бекенд-OpenAPI — чисті.** Переробка під-вʼюхи
  «Проекти → TimeCamp»: прибрано авто-синк + лінива
  загрузка по під-вʼюхах (одна сторінка = один запит, Jira-проекти лише при
  переході на вкладку Jira; 6→1 запит), дерево за `parent_id` + кольори
  (`color`), архівні тьмяні, попап налаштувань синку (тогл + select задачі з
  пошуком) замість інлайн-тогла, назва+колір змапованої Jira-задачі (закриті
  тьмяні), окрема явна кнопка синку. BREAKING `GET /tc-projects` (без `start`/
  `end`/`entries_count`; +`parent_id`/`color`/`issue_name`/`issue_active`/фільтр
  `active`); `GET /jr-issues` +пошук `q`/`limit`/`active` (дефолт `limit=10`).
  Без alembic-міграції (head `10b7dc50b00f`). Backend: новий
  `app/core/utils/issue_status.py`, правки `tc_projects`/`jr_issues`
  роутерів+схем+`jr_issues_dao`. Frontend: новий `lib/tree.ts` +
  `components/projects/SyncSettingsModal.vue`, переписані `TcProjects`/
  `ProjectsView`, store `tables.ts` (loaders по під-вʼюхах + `syncProjects`/
  `saveTcSync`/`jrIssueSearch`). 3 MODIFIED capability:
  `api-tc-projects-management`, `api-jira-read`, `frontend-data-tables`. Рішення
  — `decisinLog.md` → D-017. **Уточнення за фідбеком:** фільтр — за `is_sync`
  (клієнтський, не `is_archived`), + швидке поле пошуку по локальних даних, тег
  задачі біля назви, кнопка синку — лише сервіс активної під-вʼюхи.
- [`extract-projects-screen`](../../openspec/changes/archive/2026-06-13-extract-projects-screen/)
  — **заархівовано 2026-06-13 (17/20; секції 5.2–5.4 — браузерний QA — на живу
  перевірку). 3 capability-дельти злиті в `openspec/specs/` і канонічні:
  MODIFIED `web-app-shell`, `frontend-data-tables` (+ADDED «Екран «Проекти»»),
  `frontend-app`.** Фронтенд-онлі: винесено «Проекти»-таблиці (TimeCamp+Jira) з
  `/timecamp`/`/jira` у новий екран «Проекти» з вкладеними маршрутами
  `/projects/timecamp`·`/projects/jira` (`/projects` → редірект); `/timecamp` →
  лише незіставлені записи, `/jira` → лише задачі (обидва без `Tabs`). У навігації
  — **єдиний пункт «Проекти»** першим у секції «Дані» (під-вʼюхи TimeCamp/Jira —
  таби всередині екрана); пункти «Даних» → «TimeCamp · Записи»/«Jira · Задачі».
  Реалізація: `lib/nav.ts` (`NavItem.path/children`, `leafItems`),
  `router/index.ts` (вкладений `/projects` + redirect), `views/ProjectsView.vue`
  + `views/projects/{TcProjects,JrProjects}.vue`, спрощені `TimeCampView`/
  `JiraView`, `AppShell` (один лінк + active за `route.matched`),
  `stores/tables.ts` (авто-синк по
  екранах: `autoSyncProjects`/`autoSyncEntries`/`autoSyncIssues`), `i18n`.
  Бекенд не зачіпається. `npm run build` чисто; `validate --strict` — OK.
  Дельти capability: `frontend-data-tables`, `web-app-shell`, `frontend-app`.
  Деталі — `activeContext.md`. Лишилось: браузерний QA + git-commit.
- **Веб-UI за дизайном Sync Work — 3 зміни (2026-06-13; усі
  `validate --strict` валідні):**
  - [`add-web-ui-foundation`](../../openspec/changes/archive/2026-06-13-add-web-ui-foundation/)
    — **заархівована 2026-06-13** (44/44 задачі; браузерний QA підтверджено
    робочим end-to-end — логін/пароль + Google-вхід; код у робочому дереві,
    лишився git-commit). Дизайн-система +
    app shell + авторизація (Google popup/`code` + One Tap, серверна верифікація
    `google-auth`, match-by-email, колонка `api_users.email`, alembic head
    `c03728fbb1cf`, єдиний JWT). 5 capability злиті в `openspec/specs/` і
    канонічні: **нові** `web-design-system`, `web-app-shell`, `web-auth`,
    `api-google-auth` + **MODIFIED** `frontend-app`. Рішення — `decisinLog.md`
    → D-013 (Google-вхід), D-014 (front HTTP-клієнт: authed-by-default +
    токен через DI-provider).
  - [`add-calendar-timesheet`](../../openspec/changes/archive/2026-06-13-add-calendar-timesheet/)
    — **заархівовано 2026-06-13** (read-only візуалізація, D-016; реалізація +
    браузерний QA пройдено наживо). `GET /calendar` (read поверх
    `tc_entries`⋈`tc_projects`⋈WST, **без міграції**, alembic head
    `10b7dc50b00f`) + фронт-екран тижня (сітка, блоки 3 варіанти, стани
    `service`/`tempo`/`synced` + `failed` forward-compat, тулбар, фільтри,
    навігація тижнями, тоталі, панель деталей-перегляд). Backend:
    `routers/calendar.py`, `schemas/calendar.py`, `TCEntriesDAO.get_calendar_blocks`.
    Frontend: `CalendarView` + `components/calendar/*` + `stores/calendar.ts` +
    `lib/calendar.ts` + `styles/calendar.css` + `api.calendar`. `npm run build`
    чисто; 401-контракт перевірено. **2 нові capability злиті в `openspec/specs/`
    і канонічні: `api-calendar`, `frontend-calendar`.** Редагування/sync/round-trip
    і колонка `billable` — у майбутні `add-calendar-editing` /
    `add-worklog-update-flow`.
  - [`add-data-screens`](../../openspec/changes/archive/2026-06-13-add-data-screens/) —
    **заархівовано 2026-06-13** (29/35; секція 9 QA — частково живцем, решта
    відкладена). Backend: Users CRUD (invite без пароля → Google; `password_hash
    → nullable`, alembic head `10b7dc50b00f`), Jira-read (`GET /jr-issues`, `PATCH
    /jr-projects/{id}`); smoke 16/16 PASS. Frontend: каркас таблиць + 5 екранів +
    stores; `npm run build` чисто; період читання 6 міс + авто-синк при відкритті.
    Ім'я користувача = наявний `username` (без колонки `name`, D-015). **5 нових
    capability злиті в `openspec/specs/`** (`frontend-data-tables`,
    `frontend-sync-journal`, `frontend-users`, `api-users-management`,
    `api-jira-read`) і канонічні.
  - Відкладено окремими майбутніми змінами: RBAC-ролі, untracked→issue
    matching, редагування календаря (`add-calendar-editing`), update/delete
    worklog-ів у Tempo (`add-worklog-update-flow`).
- [`restructure-monorepo-frontend`](../../openspec/changes/archive/2026-06-12-restructure-monorepo-frontend/)
  — заархівована **2026-06-12** (end-to-end запуск підтверджено). Монорепо:
  бекенд `api/` (пакет `app`, переїхав із `src/`), фронт `front/` (Vue 3 +
  Vite + TS, vue-router, Pinia, `fetch`), мультисервісний Docker на корені з
  dev hot-reload, host-nginx на доменах `sync.loc`/`sync.dev`, дворівневі
  інструкції агентів, host-порти за конвенцією (продукт 33: api `10331`,
  front `10332`, db `11331`). Доменна логіка/схема БД не зачіпались (alembic
  head `ef2c7288bbb0`). 4 capability злиті в `openspec/specs/`
  (`monorepo-layout`, `frontend-app`, `container-orchestration`,
  `workspace-conventions`). Деталі — `decisinLog.md` → D-012.
- [`add-rest-api`](../../openspec/changes/archive/2026-06-12-add-rest-api/)
  — заархівована **2026-06-12**: REST API підтверджено робочим, 5
  capability-специфікацій злиті в `openspec/specs/`. Тех-довідка —
  `docs/technical/api-reference.md`.

## Що працює (HTTP API)

- FastAPI app (`app/api/app.py`) із CORS і глобальними exception handler-ами.
  Старт — `run_api.py` / `make serve` (підтверджено робочим 2026-06-12).
- JWT auth (`/auth/login`, `/auth/refresh`, `/auth/me`) поверх `api_users`;
  паролі хешуються прямим `bcrypt` (`app/api/auth.py`, формат `$2b$`).
- `api_jobs` lifecycle (`running → needs_verification → verified`, або
  `running → failed`) — wrapper `app/api/jobs_wrapper.run_job`.
- Read-endpoints: `/tc-projects` (з `entries_count`), `/jr-projects` (з
  `issues_count`), `/worklog-sync-tasks` (із summary), `/tc-entries/untracked`.
- PATCH `/tc-projects/{id}` з `extra=forbid` і регексом для `issue_key`.
- 8 sync-trigger endpoint-ів з опційним `?background=true`.

## Що не реалізовано

- Сценарій оновлення (`pre_update → update → updated`) і видалення раніше
  створених worklog-ів у `Tempo` — статуси оголошені, логіки немає; винесено в
  майбутню `add-worklog-update-flow` (активується редагуванням/видаленням
  `synced`-блоку календаря).
- Редагування календаря (CRUD блоків, drag/resize/split/duplicate/delete,
  per-block і масовий sync, колонка `billable`) — майбутня `add-calendar-editing`
  (календар поки read-only, D-016).
- Тести (юніт/інтеграційні) і CI.
- Повноцінне управління користувачами — **частково закрито** зміною
  `add-data-screens`: є CRUD через API (`GET/POST/PATCH/DELETE /users`, invite
  без пароля → Google) + CLI `add_user`. Лишилось окремою зміною
  `add-user-management-cli`: set-password через API, CLI list/deactivate.
- TTL/cron для старих `api_jobs` — `add-api-jobs-cleanup`.
- RBAC, per-user OAuth-токени на Jira/TimeCamp — окремі майбутні зміни.

## Поточний стан гілки

- Branch: `main`.
- Незакомічене: `M main.ipynb` (зміна періоду на 2026-04-08…2026-04-13)
  плюс імпементація `add-rest-api` (нові файли `app/api/`, `app/models/api_*.py`,
  `app/dao/api_*_dao.py`, `run_api.py`, alembic-ревізія `ef2c7288bbb0`),
  а також сесія 2026-06-12: `app/cli/`, `Makefile`, `.python-version` (3.14),
  перехід `passlib → bcrypt` у `pyproject.toml`/`app/api/auth.py`,
  міграція `poetry → uv` (`uv.lock`).
- Остання міграція: `10b7dc50b00f` (2026-06-13, `make_password_hash_nullable_api_users`;
  попередня — `c03728fbb1cf` `add_email_to_api_users`). Застосовано.
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
