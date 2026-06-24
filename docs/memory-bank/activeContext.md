# Active Context

## Заархівована зміна: `rework-jira-issues-screen` (2026-06-23)

**Реалізовано і заархівовано 2026-06-23 (24/24; браузерний QA підтверджено
користувачем — «все працює»). Дельти злиті в `openspec/specs/`: `api-jira-read`
(MODIFIED «Список Jira-задач» → `updated`-вісь+пагінація, ADDED «Перелік статусів
Jira-задач»), `frontend-data-tables` (MODIFIED «Екран Jira»). `npm run build`
чисто; `validate --strict` OK.** Тека —
[`archive/2026-06-23-rework-jira-issues-screen/`](../../openspec/changes/archive/2026-06-23-rework-jira-issues-screen/).
Дзеркало `rework-timecamp-entries-screen` на екран **`/jira`** (задачі): читати
**лише з локальної БД**, авто-синк при відкритті (`autoSyncIssues`) **прибрано**,
**явна** кнопка синку, фільтри (проект / статус / пошук за назвою), фільтр за
**періодом активності** (`updated_at` — пост-QA пивот із `created_at`; той самий
`PeriodPicker`, дефолт екрана — поточний рік) і серверна пагінація. Порядок колонок
— **проект → тип → статус → номер (`key`) → опис**. Синк (одна кнопка-попап) тепер
виконує **витяг задач за період** (`POST /sync/jira/issues-all`, зміна
`add-jira-full-issue-pull`), а **не** projects+worklogs. На цьому екрані
`SyncState`/`SyncFilter` **не** застосовуються (немає бінарного стану синку —
браузер задач). **Без alembic** (head `10b7dc50b00f`).

**Реалізація:**
- **Backend (`api/`):** новий спільний `app/api/period.py` (`current_month` /
  `period_or_400`, винесено зі `sync_status.py` — той тепер імпортує через alias);
  `schemas/jr_issues.py` — обгортка `JRIssuesPage { items, total }`;
  `dao/jr_issues_dao.py` — `list_paginated` (фільтри період/`project_id`/`status`/
  `q`, фільтр/сорт за `updated_at DESC NULLS LAST`, `limit`/`offset` + окремий
  `COUNT`) і `distinct_statuses`; `routers/jr_issues.py` — `GET /jr-issues` →
  `response_model=JRIssuesPage` (params `updated_from`/`updated_to`, дефолт —
  поточний місяць, кап `limit`≤200) + новий `GET /jr-issues/statuses`. **BREAKING**
  контракт `GET /jr-issues`
  (плоский список → `{ items, total }`). OpenAPI на живому контейнері підтверджує
  новий шейп; 401-гейт ок.
- **Frontend (`front/`):** `api/types.ts` (`JRIssuesPage`); `api/client.ts`
  (`jrIssues` → `JRIssuesPage` з `updatedFrom`/`updatedTo`/`status`/`offset`;
  новий `jrIssueStatuses`); `stores/tables.ts`
  (стан `jrPeriod`/`jrStatus`/`jrProjectFilter`/`jrQuery`/`jrOffset`/`jrTotal`/
  `jrStatusOptions` + `loadJrIssues`/сетери з reset пагінації; **видалено**
  `autoSyncIssues`/`loadIssues`); новий
  `components/data/FilterSelect.vue` (поповер за патерном `Menu.vue`, `searchable`-
  проп, опція «усі»); `components/jira/SyncIssuesModal.vue` (попап витягу задач за
  період); переписаний `views/JiraView.vue` на `DataPage` (тулбар:
  `PeriodPicker` + 2 `FilterSelect` + пошук; пагінація; одна кнопка-попап); i18n
  (UK+EN); CSS `.fsel*`/`.jrbar` у `data.css`.
- **Рішення користувача (мапінг-select):** `jrIssueSearch` шукає серед **усіх**
  задач — передає широкий період (`updatedFrom='2000-01-01'`,
  `updatedTo='2999-12-31'`); задачі з `NULL updated_at` у пошук не потраплять.

**Пост-QA рефінмент (фідбек користувача наживо):** (1) випадайка фільтра проекту —
**лише відстежувані** (`is_watched`), бо за несинкованими проектами фільтрувати
сенсу немає; (2) **дефолт періоду екрана** змінено з «поточний місяць» на
**«поточний рік»** (`defaultIssuePeriod`) + додано пресет «Цей рік» у `PeriodPicker`
— місяць виявився завузьким для браузера задач; (3) фікс `FilterSelect`: пункти —
`flex: none` (у скрольному `flex-column` флекс стискав їх до кількох px). Спека
`frontend-data-tables` і `design.md` (D3/D5) оновлені; `validate --strict` OK,
`npm run build` чисто.

**Важливе про покриття даних (зʼясовано на QA, джерело плутанини):** `jr_issues`
наповнюється **лише як побічний ефект синку worklog-ів** (`update_worklog →
update_jira_issues`) + точкового синку за ключами — це **НЕ** повний витяг усіх
задач із Jira. Тож локально є тільки задачі, на які синкнулись worklog-и (звідси й
не-заасайнені на користувача задачі), а створені-але-не-залогані задачі локально
відсутні (на момент QA — 300 задач: 2024→91, 2025→161, 2026→46; `created_at` усюди
не-NULL; закриті `Готово`=212 присутні, фільтр їх не ховає). Жодна зміна фільтра
цього не виправить — дані треба спершу синкнути. **→ Заскоуплено окремою зміною
[`add-jira-full-issue-pull`](#активна-зміна-openspec-add-jira-full-issue-pull-proposal)**
(див. нижче).

Деталі (рішення) — `design.md` (D1–D9) у теці архіву.

## Заархівована зміна: `add-jira-full-issue-pull` (2026-06-23)

**Реалізовано і заархівовано 2026-06-23 (16/16; браузерний QA підтверджено
користувачем — «все працює»). Дельти злиті в `openspec/specs/` (ADDED): 
`api-sync-triggers` («Повний синк задач Jira…» → `POST /sync/jira/issues-all`),
`frontend-data-tables` («Витяг задач Jira за період активності»). `validate --strict`
OK.** Тека —
[`archive/2026-06-23-add-jira-full-issue-pull/`](../../openspec/changes/archive/2026-06-23-add-jira-full-issue-pull/).
Наслідок QA `rework-jira-issues-screen`:
`jr_issues` наповнюється лише задачами з Tempo-worklog-ів, тож «звичайні»/не-
залогані/не-заасайнені задачі локально відсутні. Ця зміна додає **витяг задач
відстежуваних проектів** (`is_watched`) **за період активності** (`updated`).

**Реалізація:**
- **Backend (`api/`):** `JiraService` — спільний `_parse_issue` (з фіксом бага
  `creator`/`reporter` + null-safety), пагінований `_search(jql, page_size)`
  (`startAt`/`maxResults`; навіть key-based `search_issues` тепер пагінує),
  публічний `search_issues_by_projects(keys, updated_from, updated_to)` (JQL
  `project in ("KEY",…) AND updated >= … AND updated <= "… 23:59" ORDER BY updated
  DESC`); `JRProjectDAO.watched_keys(db)`;
  `UpdateJiraTask.update_issues_for_watched_projects(updated_from, updated_to)`
  (watched-ключі → витяг → upsert `JRIssuesDAO.sync_by_key`, не full-replace;
  повертає к-сть); `routers/sync_triggers.py` — `_do_jr_issues_all(payload)`
  + `POST /sync/jira/issues-all` (опційний `PeriodBody`, run_job, опц.
  `background`). Без alembic.
- **Frontend (`front/`):** `api.syncJrIssuesAll(period)`; стор-дія
  `syncJrIssuesAll(period)` (виклик → reload `loadJrIssues`; помилку кидає, щоб
  попап показав); **єдина** кнопка синку у `#actions` `JiraView` (`cloudDown`) →
  відкриває `SyncIssuesModal` (`PeriodPicker`) → витяг за період. (Окрему
  `cloudDown`-кнопку прямого витягу й period-worklog-потік `syncJrIssues`
  **прибрано** — звели в одну дію.) i18n `jr_sync`/`jrsync_*` (UK+EN).
- **Рішення:** період — **за `updated`** (активність), не `created`/«все» — синк і
  екран показують те, з чим працювали у вікні; без фільтра за worker_key/assignee
  (тягнемо й чужі задачі); скоуп — лише watched-проекти; період береться з **попапа**;
  дельти additive (ADDED-вимоги до `api-sync-triggers` + `frontend-data-tables`).

Деталі (рішення) — `design.md` (D1–D7) у теці архіву.

## Дата оновлення

2026-06-23 — **зміни `rework-jira-issues-screen` і `add-jira-full-issue-pull`
заархівовано** (обидві — браузерний QA підтверджено користувачем). Екран `/jira`:
читання з локальної БД за період **активності** (`updated_at`, дефолт — поточний
рік), фільтри (проект `is_watched` / статус / пошук) + серверна пагінація + **одна**
кнопка-попап, що тягне з Jira всі задачі watched-проектів, активні в періоді
(`POST /sync/jira/issues-all`, JQL `updated`, без фільтра за користувачем). 4 дельти
злиті в `openspec/specs/`: `api-jira-read` (MODIFIED+ADDED), `api-sync-triggers`
(ADDED), `frontend-data-tables` (MODIFIED+ADDED). Деталі — нижче.
2026-06-23 — **зміну `rework-timecamp-entries-screen` заархівовано** (27/27 задач;
браузерний QA підтверджено користувачем). Дельти злиті в `openspec/specs/`:
`api-sync-status` (ADDED `GET /tc-entries`), `frontend-data-tables` (MODIFIED
«Екран TimeCamp» + ADDED «Єдине відображення стану синку»). Деталі — нижче.
2026-06-13 — **фази 1, 2 і 3 заархівовані**; код усіх у робочому дереві, не закомічено. Фаза 2 (`add-calendar-timesheet`, read-only візуалізація, D-016)
— **реалізована, браузерний QA пройдено наживо, заархівована 2026-06-13**;
2 нові capability злиті в `openspec/specs/` і канонічні: `api-calendar`,
`frontend-calendar`. Лишився лише git-commit.

## Заархівована зміна: `rework-timecamp-entries-screen` (заархівовано 2026-06-23)

**Реалізовано і заархівовано 2026-06-23 (27/27 задач; браузерний QA підтверджено
користувачем). `npm run build` чисто; backend live smoke + DAO-перевірка PASS;
`validate --strict` — OK. 2 дельти злиті в `openspec/specs/` і канонічні:
`api-sync-status` (ADDED `GET /tc-entries`), `frontend-data-tables` (MODIFIED
«Екран TimeCamp» + ADDED «Єдине відображення стану синку»).** Тека —
[`archive/2026-06-23-rework-timecamp-entries-screen/`](../../openspec/changes/archive/2026-06-23-rework-timecamp-entries-screen/).
Переробка екрана **`/timecamp`**: був показ лише незіставлених записів
(`GET /tc-entries/untracked` із захардкодженим `meta IS NULL` + немаплений проект),
період зашито (6 міс), без пагінації, синк — авто у фоні при відкритті. Стало:
**усі** записи з локальної БД за обраний період, серверна пагінація, фільтр стану
синку, **явна** кнопка синку з попапом.

**Затверджені рішення користувача (патерн на майбутнє):** (1) дані-екрани читають
**лише з локальної БД**; синк — **тільки** явною кнопкою з вибором періоду;
**авто-синк при відкритті прибрано** (згодом — синк за розкладом). Той самий патерн
далі до **`/jira`** і **`/tempo`** окремими змінами (auto-memory
`data-pages-no-auto-sync`). (2) «Синхронізовано» — **бінарно**: запис synced, якщо
є `worklog_sync_task` у `created`/`updated` (worklog у Tempo), scoped по `worker_key`
(як `GET /calendar`).

**Реалізація:**
- **Backend (`api/`, без alembic-міграції, head лишився `10b7dc50b00f`):** новий
  `GET /tc-entries` у `routers/sync_status.py` (`list_tc_entries`; дефолт періоду —
  поточний місяць через `_current_month()`; `synced=all|synced|unsynced`;
  `limit` 50/кап 200; `offset`; валідація `start<=end` через `_period_or_400`).
  `TCEntriesDAO.list_with_sync_state` — `tc_entries` ⋈ `tc_projects` + похідний
  `is_synced` через **EXISTS** на `worklog_sync_tasks` (`created`/`updated`, scoped
  по `worker_key` — чужий стан не протікає, `worker_key=None`→усе unsynced); фільтр
  стану, сорт `start_at DESC`, серверна пагінація, окремий `COUNT` для `total`;
  `issue_key` резолвиться в роутері (`meta.task`→`tc_project.issue_key`). Схеми
  `TCEntryItem`/`TCEntriesResponse` у `schemas/sync_status.py`.
  `GET /tc-entries/untracked` **незмінний** (під майбутній matching). Live smoke
  (token під наявного user-а) + DAO-перевірка на `worker_key='JIRAUSER10303'`
  (2819/3391 synced; інваріант synced+unsynced==all; scoping OK) — PASS.
- **Frontend (`front/`):** `api/types.ts` (`TCEntry`/`TCEntriesResponse`/
  `TCSyncFilter`), `api/client.ts` (`tcEntries({start,end,synced,limit,offset})`),
  `lib/period.ts` (**спільний** `PERIOD_PRESETS` + `defaultReviewPeriod`= «цей
  місяць», D6 — переюз picker'ом і попапом), `stores/tables.ts` (стан
  `tcEntries/tcPeriod/tcSyncFilter/tcOffset/tcTotal/tcPageSize`,
  `loadTcEntries`/`setTcPeriod`/`setTcSyncFilter`/`setTcOffset`/`syncTcEntries`;
  **прибрано** `loadUntracked`/`autoSyncEntries`/`tcUntracked`),
  `components/timecamp/SyncEntriesModal.vue` (`Sheet`+`PeriodPicker`), переписано
  `views/TimeCampView.vue` на `DataPage`, i18n (UK+EN), CSS у `data.css`.
  MODIFIED capability: `api-sync-status`, `frontend-data-tables`.
- **UI-рефінмент за фідбеком (D9):** компактний **`components/data/PeriodPicker.vue`**
  (одна кнопка → dropdown зі швидкими шаблонами всередину + ручні дати; поповер за
  патерном `Menu.vue`, **без зовнішньої бібліотеки** — фронт тримає лише
  `vue`/`vue-router`/`pinia`), переюзаний і тулбаром, і попапом синку; фільтр стану
  синку — наявний `Segmented` (як на `/projects/timecamp`), усі контроли зліва;
  стан синку в таблиці — спочатку іконкою, далі (D11) зведено до спільного
  компонента; **задача — окрема колонка** (`issue_key` key-pill).
- **Уніфікація «мови синку» + колонки/дата (D10/D11):** порядок колонок `/timecamp`
  — **Проект → Задача → Опис → Дата → Час → Стан синку**; дата — `дд.мм.рррр`
  (`lib/format.ts → fmtDate`). Два спільні компоненти `components/data/SyncState.vue`
  (крапка + підпис `Synced`/`Not synced`) і `SyncFilter.vue` (`Segmented`
  `All|Synced|Not synced`, канонічний `SyncTri`) — **ідентичні на всіх дані-екранах**;
  переведено `/timecamp`, `/projects/timecamp`, `/projects/jira` (видалено локальні
  `.tct__state`/`.tcst` і per-екранні `Segmented`-опції; `tcActive`/`jrActive`→`SyncTri`;
  прибрано мертві i18n-ключі `flt_*`/`sync_state_*`/`tc_flt_*`). Підписи — англійською
  в обох локалях (захардкоджено). Патерн зафіксовано в `systemPatterns.md` («Єдина
  мова синку») + auto-memory `sync-status-unified-ui`. Рішення — `design.md` (D1–D11).

## Заархівована зміна: `rework-jira-projects-subview` (2026-06-14)

**Реалізовано і заархівовано 2026-06-14 (11/12 задач; 5.2 — браузерний QA —
лишився на живу перевірку). `validate --strict` — OK; `npm run build` — чисто.
Дельта злита в `openspec/specs/frontend-data-tables/` (MODIFIED «Екран «Проекти»»
+ ADDED «Попап налаштувань синку Jira-проекту»).** Тека —
[`archive/2026-06-13-rework-jira-projects-subview/`](../../openspec/changes/archive/2026-06-13-rework-jira-projects-subview/).
Дзеркало TimeCamp-рішень `rework-projects-screen` на під-вʼюху **«Проекти → Jira»**
(`/projects/jira`), **фронтенд-онлі**: (1) **фільтр** за станом синку `усі | у
синку | не в синку` за `is_watched` (клієнтський, без re-fetch); (2) **швидкий
пошук** по локальних даних (`key`/`name`); (3) **попап редагування** замість
інлайн-тогла (шестерня / подвійний клік) — **простіший за TimeCamp: лише тогл
`is_watched`**, без select-а задачі, **Save завжди дозволено** (Jira-проект не
мапиться на задачу); (4) архівні — тьмяні; (5) `issues_count` лишається, рахує
**всі** задачі. **Без дерева/кольору/тега** (Jira-проекти плоскі — нема
`parent_id`/`color`/маппінгу). Бекенд НЕ чіпаємо (`GET /jr-projects` уже віддає
все; `PATCH /jr-projects/{id}` приймає `is_watched`). MODIFIED capability
`frontend-data-tables` (Jira-частина «Екран «Проекти»» + нова вимога «Попап
налаштувань синку Jira-проекту»). Рішення — `design.md` (D1–D5).

**Реалізація (frontend, `front/`):** `stores/tables.ts` (новий `jrActive`
фільтр-стан; `toggleJrWatched` → `saveJrWatched(id, is_watched)`); нова
`components/projects/JrSyncSettingsModal.vue` (Sheet-попап з **одним тоглом**,
Save завжди дозволено); переписано `views/projects/JrProjects.vue` — плоский
список (переюз `.tct*`-стилів, без дерева/кольору) з тулбаром (фільтр + пошук),
індикатором стану синку, шестернею, подвійним кліком, тьмяними архівними,
лічильником задач (новий `.tct__count`). i18n — **усі ключі переюзані**, нових
рядків не треба. Бекенд не зачіпався. `npm run build` чисто. Лишилось:
браузерний QA (5.2) + git-commit.

## Заархівована зміна: `add-page-shell-template` (2026-06-13)

**Реалізовано і заархівовано 2026-06-13 (12/13 задач; 4.2 — браузерний QA —
лишився на живу перевірку). `validate --strict` — OK; `npm run build`
(`vue-tsc`+`vite`) — чисто. Нова capability `frontend-page-shell` (3 вимоги)
злита в `openspec/specs/` і канонічна.** Тека —
[`archive/2026-06-13-add-page-shell-template/`](../../openspec/changes/archive/2026-06-13-add-page-shell-template/).
Винесено **єдиний переюзовний каркас сторінки** `components/data/DataPage.vue`
для всіх дані-/табличних екранів (раніше кожна в'юха копіпастила `.page` →
`PageHeader` → опц. суб-бар → банер `data-error` → `.page__body`). `DataPage`
інкапсулює це: props `title`(req)/`desc?`/`error?` + **закладки** (`tabs`/
`activeTab` + `update:activeTab`, окремі під-сторінки, **router-agnostic** —
навігацію робить в'юха, як Projects TimeCamp/Jira), слоти `#actions` (верхній
правий кут), `#toolbar` (опц. суб-бар), default (тіло в `.page__body`); банер
помилки — авто за prop `error`. Порядок: заголовок → закладки → тулбар → банер →
тіло.

**Реалізація:** новий `components/data/DataPage.vue` (поглинув `PageHeader` +
банер помилки + рендер `Tabs`); 6 в'юх переведено на нього (`ProjectsView` —
показовий приклад закладок через `:tabs`/`v-model:active-tab`; `TimeCampView`/
`JiraView` — без actions/toolbar; `TempoView` — `#toolbar`=`.pipe`; `JournalView`
— `#toolbar`=chips + `Sheet` у тілі; `UsersView` — `#actions`=додати + `Sheet`-
форма в тілі); `PageHeader.vue` **видалено** (0 зовнішніх споживачів). Стилі —
наявні `.page*`/`data-error` (без нових CSS). `CalendarView` (власний `.cal`-
layout) — поза скоупом (інший клас екрана, D5). Нова canonical-capability
`frontend-page-shell`. Рішення — `design.md` (D1–D7). Лишилось: браузерний QA +
git-commit. Мета — далі **постійно** перевикористовувати каркас для нових таблиць.

## Заархівована зміна: `rework-projects-screen` (2026-06-13)

**Реалізовано і заархівовано 2026-06-13 (26/27 задач; 11.2 — браузерний QA —
лишився на живу перевірку; git-commit). `validate --strict` — OK; `npm run
build` і бекенд-контракт (OpenAPI) — чисті. 3 capability-дельти злиті в
`openspec/specs/` і канонічні: MODIFIED `api-jira-read` (пошук `q`/`limit` +
`active`), ADDED у `api-tc-projects-management` (GET-дерево + фільтр архіву),
MODIFIED+ADDED `frontend-data-tables` (екран «Проекти» + попап синку).** Тека —
[`archive/2026-06-13-rework-projects-screen/`](../../openspec/changes/archive/2026-06-13-rework-projects-screen/).
Переробка під-вʼюхи **«Проекти → TimeCamp»**: відкриття екрана робило **6 запитів**
(2 GET даних + 2 POST авто-синку + 2 GET reload) — авто-синк прибрано повністю,
а дані вантажить **кожна під-вʼюха сама** (TimeCamp → лише `GET /tc-projects`;
Jira-проекти — лише при переході на вкладку Jira), тож відкриття сторінки: **6→1**
запит. TimeCamp-проекти стали **деревом** (`parent_id`) з кольором
(`color`); архівні — тьмяні; інлайн-тогл `is_sync` замінено **попапом
налаштувань** (тогл синку + select задачі з пошуком, Save заблоковано без задачі);
маппінг показує **назву** Jira-задачі тінтовану кольором проекту (закриті задачі
тьмяні); синк проектів — **окрема явна кнопка**, ніколи не авто. **BREAKING-контракт
`GET /tc-projects`:** прибрано `start`/`end` і `entries_count`, додано
`parent_id`/`color`/`issue_name`/`issue_active` + фільтр `active=active|inactive|all`;
`GET /jr-issues` отримав пошук `q`/`limit` + похідний `active`. **Без alembic-міграції**
(усі колонки вже є). 3 MODIFIED capability: `api-tc-projects-management` (+GET-вимога),
`api-jira-read` (пошук+`active`), `frontend-data-tables` («Екран «Проекти»»: дерево/
попап/без авто-синку). Рішення — `design.md` (D1–D10) і Memory Bank → **D-017**.

**Реалізація:**
- **Backend (`api/`):** новий `app/core/utils/issue_status.py`
  (`is_issue_active` + `DONE_STATUSES`, спільний для обох endpoint-ів);
  `schemas/tc_projects.py` — `TCProjectItem` (дерево+маппінг, без
  `entries_count`); `routers/tc_projects.py` — GET без `start`/`end`, LEFT JOIN
  `jr_issues`, фільтр `active`, PATCH повертає той самий повний шейп з резолвом;
  `schemas/jr_issues.py` — `computed_field active`; `routers/jr_issues.py` +
  `dao/jr_issues_dao.py` `list_filtered` — `q`/`limit` (дефолт 10, кап ≤50).
- **Frontend (`front/`):** `api/types.ts` (`TCProject` дерево-поля,
  `JRIssue.active`); `api/client.ts` (`tcProjects(active?)`, `jrIssues({q,limit})`);
  `stores/tables.ts` — прибрано `autoSyncProjects`/`loadProjects`/`toggleTcSync`,
  додано `loadTcProjects`/`loadJrProjects` (ідемпотентні, по під-вʼюхах),
  `saveTcSync`, `jrIssueSearch`, `syncProjects` (явна кнопка); новий
  `lib/tree.ts` (`buildTree`/`flattenTree`/`safeColor`, orphan-hoisting); нова
  `components/projects/SyncSettingsModal.vue` (Sheet-попап); переписано
  `views/projects/TcProjects.vue` (дерево/тег/фільтр/попап) і `ProjectsView.vue`
  (без авто-load, ліниві лічильники, кнопка синку); `JrProjects.vue` (власний
  `loadJrProjects` на mount); `styles/data.css` (`.tct*`/`.ssm*`); `i18n` (UK+EN).
  Побічно: `JiraView` тепер просить `jrIssues({limit:50})`, бо дефолт `/jr-issues`
  став 10. Продуктові розвилки підтверджено користувачем (прибрати
  `entries_count`/date-фільтр; синк лише кнопкою; тьмянити і архівні TC-проекти,
  і закриті Jira-задачі).
- **Уточнення за фідбеком користувача (та сама сесія, після першої реалізації;
  деталі — `decisinLog.md` → D-017):** (1) фільтр під-вʼюхи TimeCamp — за станом
  синку (`is_sync`), **клієнтський** (не `is_archived` серверний; бекендний
  `active`-param лишився як опційна можливість API, UI його не використовує);
  (2) додано **швидке поле пошуку** по локальних даних (`name`/`issue_key`/
  `issue_name`); (3) тег задачі перенесено **одразу до назви** проекту;
  (4) кнопка синку синкає **лише сервіс активної під-вʼюхи** (TimeCamp ↔ Jira,
  деривація з `route.name`). `npm run build` лишається чистим.

## Заархівована зміна: `extract-projects-screen` (2026-06-13)

**Створено, реалізовано і заархівовано 2026-06-13 (17/20 задач; секції 5.2–5.4
— браузерний QA — лишилися на живу перевірку). 3 capability-дельти злиті в
`openspec/specs/` і канонічні: MODIFIED `web-app-shell` (секція «Дані» з пунктом
«Проекти» + вкладена маршрутизація `projects/*`), MODIFIED `frontend-data-tables`
(ADDED «Екран «Проекти»», спрощені «Екран TimeCamp»/«Екран Jira» без вкладок),
MODIFIED `frontend-app` (вкладені `projects/*` + редірект). Тека —
[`archive/2026-06-13-extract-projects-screen/`](../../openspec/changes/archive/2026-06-13-extract-projects-screen/).**
Фронтенд-онлі рефактор
навігації/роутингу: винесено дві «Проекти»-таблиці (TimeCamp + Jira) з екранів
`/timecamp` і `/jira` у новий екран **«Проекти»** з вкладеними маршрутами
`/projects/timecamp` і `/projects/jira` (`/projects` → редірект на дефолт).
Після виносу `/timecamp` показує лише незіставлені записи, `/jira` — лише
задачі (обидва без `Tabs`). Навігація: **єдиний пункт «Проекти»** першим у
секції «Дані» (→ `/projects`; під-вʼюхи TimeCamp/Jira — таби всередині екрана,
не окремі пункти; рішення користувача 2026-06-13); пункти «Даних» перейменовані
під вміст («TimeCamp · Записи», «Jira · Задачі»). Бекенд/DAO/схема БД **не зачіпались**
(переюз наявних `GET/PATCH /tc-projects`, `/jr-projects`,
`GET /tc-entries/untracked`, `GET /jr-issues`, `POST /sync/...`).
`validate --specs --strict` — 20/20 OK.

**Реалізація (frontend, `front/`):**
- `lib/nav.ts` — `NavItem` отримав опційні `path`/`children`; у секцію «Дані»
  додано єдиний пункт `projects` (першим) із children `projects-timecamp`/
  `projects-jira`; `children` живлять **лише роутер**; хелпер `leafItems()`
  (тільки для `SCREENS` → валідні екрани-«листки» для `validScreen`).
- `router/index.ts` — узагальнений `routeFor()` будує вкладений `/projects`
  (контейнер + `redirect` на першу під-вʼюху + дочірні з абсолютними шляхами);
  решта екранів — плоскі, як раніше.
- Нові `views/ProjectsView.vue` (контейнер: `PageHeader` + `Tabs`, привʼязані
  до маршруту, + `<router-view>`), `views/projects/TcProjects.vue`,
  `views/projects/JrProjects.vue` (таблиці перенесені без зміни поведінки).
- `views/TimeCampView.vue` і `views/JiraView.vue` — прибрано `Tabs` і таблицю
  проектів; лишились untracked-записи / задачі відповідно.
- `components/AppShell.vue` — рендерить `grp.items` (пункт «Проекти» — **один
  лінк** на `/projects`); активність — за `route.matched` (батьківський
  `/projects` присутній у matched на будь-якому `/projects/*`).
- `stores/tables.ts` — авто-синк роздроблено по екранах (D4): `autoSyncProjects`
  (tc+jr проекти), `autoSyncEntries` (tc-записи), `autoSyncIssues` (re-sync
  відомих ключів задач); фокусні лоадери `loadProjects`/`loadUntracked`/
  `loadIssues` замінили складені `loadTimeCamp`/`loadJira`. Кожне джерело
  синкається рівно з одного екрана; 5-хв вікно свіжості збережено.
- `i18n/strings.ts` (UK+EN) — нові ключі `nav_section_projects`,
  `nav_projects_timecamp`/`_jira`, `pr_title`/`pr_desc`; перейменовані
  `nav_timecamp`/`nav_jira`; уточнені `tc_*`/`jr_*` заголовки.
- `npm run build` (`vue-tsc --noEmit` + `vite build`) — чисто.

## Статус фази 3 (`add-data-screens`) — заархівовано 2026-06-13

Реалізовано (29/35 задач; секція 9 «ручний QA» — частково пройдено живцем, решта
відкладена). Зміна заархівована в
[`archive/2026-06-13-add-data-screens/`](../../openspec/changes/archive/2026-06-13-add-data-screens/);
**5 нових capability злиті в `openspec/specs/` і канонічні**:
`api-users-management`, `api-jira-read`, `frontend-data-tables`,
`frontend-sync-journal`, `frontend-users`. Три відкриті питання design.md
закриті рішеннями користувача (D-015): `name` → переюз `username`; `last_seen` і
точковий `ids[]` для Tempo — відкладено. Браузерний QA-рефінмент: період читання
розділено зі sync-періодом + авто-синк при відкритті (теж D-015).

- **Backend:** `api_users.password_hash → nullable` (alembic head
  **`10b7dc50b00f`**, застосовано); Users CRUD (`GET/POST/PATCH/DELETE /users`,
  invite без пароля → Google-вхід, дублі email/username → `409`, NULL-хеш login →
  `401`); Jira-read (`GET /jr-issues?project_id`, `PATCH /jr-projects/{id}` тогл
  `is_watched`). Smoke-тест 16/16 проти живої БД — PASS. Побічний фікс:
  `config.py` `extra="ignore"` (спільний `.env` з `VITE_*` ламав локальний
  старт). Рішення — `decisinLog.md` → **D-015**.
- **Frontend:** табличний каркас (`DataTable` generic, `Tabs`, `PageHeader`,
  `StatusBadge`, `SyncBtn`, `ProjTag`), 5 екранів (TimeCamp/Jira/Tempo/Журнал/
  Користувачі), stores `tables`/`journal`/`users`, методи клієнта + типи,
  динамічний бейдг `needs_verification` у навігації, нові стилі `data.css`
  (порт `tables.css`). `npm run build` (`vue-tsc` + `vite`) — чисто.
- **Залишок:** браузерний QA (секція 9) і git-commit.

## Статус фази 1 (`add-web-ui-foundation`) — заархівована 2026-06-13

Реалізовано (44/44 задачі; браузерний QA — секція 9 — **підтверджено робочим
2026-06-13**: логін/пароль і Google-вхід працюють end-to-end). Зміна
заархівована в
[`archive/2026-06-13-add-web-ui-foundation/`](../../openspec/changes/archive/2026-06-13-add-web-ui-foundation/);
5 capability злиті в `openspec/specs/` і є канонічними: **нові**
`web-design-system`, `web-app-shell`, `web-auth`, `api-google-auth` +
**MODIFIED** `frontend-app` (auth-gated роутинг на 6 екранів).

**Операційні нюанси (Docker), доведені при ввімкненні Google-входу 2026-06-13:**
(1) `VITE_GOOGLE_CLIENT_ID` (публічний) прокинуто у front-сервіс через
`docker-compose.yml` — Vite не читає кореневий `.env`; (2) `google-auth`
довстановлено у venv api (`uv sync` у контейнері), бо анонімний `/app/.venv`-том
застарів після додавання залежності й валив старт із `ModuleNotFoundError`.
Симптоми, команди й env-розподіл — `docs/technical/dev-environment.md` (§4, §7).

- **Backend:** колонка `api_users.email` (`UNIQUE`, nullable; alembic head
  `c03728fbb1cf`, **застосовано**); `APIConfig.google_client_id/secret`;
  `APIUserDAO.get_by_email` (lower-case, лише активні); `POST /auth/google`
  (`google-auth`-верифікація credential / обмін code; match-by-email; єдиний
  JWT; `401 "account not found"`; `503` без конфігу). Рішення — `decisinLog.md`
  → **D-013**. Verified live: `503`/`422`/`401` + `code`-без-secret `503`.
- **Frontend:** дизайн-система (токени/теми/акценти/щільність, 12 UI-примітивів,
  іконки, Geist-шрифти), i18n UK/EN (`useI18n` поверх `ui.lang`), dot-path
  storage-обгортка (D7), stores `ui`/`auth`, `api/client` (authed-by-default +
  токен через DI-provider + 401-хук, **D-014**), app shell (нав-секції, collapse,
  user-chip, Tweaks), `vue-router` на 6 екранів (StubView — фази 2–3), auth-gate,
  екран входу (логін/пароль + Google popup/`code` + One Tap). `npm run build`
  (`vue-tsc` + `vite`) — чисто.
- **Залишок:** лише git-commit (реалізація + архів лежать у робочому дереві
  незакоміченими — коміт за рішенням користувача).

## Поточний фокус

**Перенесення дизайну Sync Work у фронт — 3 OpenSpec-зміни (фази 1 і 3 —
заархівовані 2026-06-13; фаза 2 — proposal).** Джерело — handoff-бандл із Claude Design, який лежить **локально в
[`docs/design/`](../design/)** (прототип React+CSS у `docs/design/project/src/*`,
наявний OpenAPI — `docs/design/project/uploads/sync.work.json`). 7 екранів:
авторизація, календар, таблиці TimeCamp/Jira/Tempo, журнал синку,
користувачі; двомовність UK/EN, світла/темна теми, Tweaks. Розбито на 3
послідовні фази:

1. [`add-web-ui-foundation`](../../openspec/changes/archive/2026-06-13-add-web-ui-foundation/)
   — **заархівована 2026-06-13.** Дизайн-система
   (токени/теми/примітиви/іконки/i18n/Tweaks), app shell
   (навігація, маршрути, auth-gate, user-chip), екран входу і **Google-вхід**
   (popup + One Tap, серверна верифікація, match-by-email до `api_users`,
   без авто-реєстрації; нова колонка `api_users.email`).
2. [`add-calendar-timesheet`](../../openspec/changes/archive/2026-06-13-add-calendar-timesheet/) —
   тижневий timesheet (головний екран), **заархівовано 2026-06-13** (read-only
   візуалізація, D-016; QA пройдено наживо; 2 capability `api-calendar`/
   `frontend-calendar` злиті в `openspec/specs/`): `GET /calendar` (read поверх наявних
   `tc_entries`/`worklog_sync_tasks`/`tc_projects`, **без міграції й нових
   колонок**, alembic head лишився `10b7dc50b00f`) + фронт-екран (сітка, блоки
   3 варіанти, стани синку `service`/`tempo`/`synced` + error-стиль `failed`
   forward-compat, тулбар, фільтри, навігація тижнями, тоталі, панель деталей у
   режимі перегляду). **Backend:** `app/api/routers/calendar.py`,
   `app/api/schemas/calendar.py`, `TCEntriesDAO.get_calendar_blocks` (LEFT JOIN
   WST за `worker_key`); деривація стану — у роутері (`failed` не віддається,
   D2). **Frontend:** `views/CalendarView.vue`, `components/calendar/*`,
   `stores/calendar.ts` (read-only), `lib/calendar.ts` (геометрія/lane-розкладка),
   `styles/calendar.css`, метод `api.calendar` + типи; роут `calendar` →
   `CalendarView`. `npm run build` (`vue-tsc`+`vite`) — чисто; 401-контракт
   `/calendar` перевірено. Редагування/створення/sync і round-trip у Tempo
   **відкладено** окремими майбутніми змінами (`add-calendar-editing`,
   `add-worklog-update-flow`). Лишилось: браузерний QA (секція 7) + git-commit.
3. [`add-data-screens`](../../openspec/changes/archive/2026-06-13-add-data-screens/) —
   **заархівовано 2026-06-13** (див. статус вище). Таблиці TimeCamp/Jira/Tempo,
   журнал `api_jobs` (з verify), користувачі + **Users CRUD** (`/users`, invite
   без пароля → вхід через Google; **ім'я = наявний `username`**, nullable
   `password_hash`) і мінімальний Jira-read (`GET /jr-issues`,
   `PATCH /jr-projects/{id}`).

**Стратегія фронту (2026-06-13, D-016):** спочатку **візуалізувати** все, що
вже є в БД (read-only екрани), потім проходитись по кожній сторінці окремо «по
цеглинці» — додавати редагування/запис на бекенд окремими змінами. Календар —
перший приклад цього підходу.

**Свідомо відкладено** (UI показує, дія вимкнена; окремі майбутні зміни):
RBAC-ролі (admin/member/viewer), untracked→issue matching; **редагування
календаря** (`add-calendar-editing`) і **update/delete worklog-ів у Tempo**
(`add-worklog-update-flow`). Активні зміни валідні
(`openspec validate --strict`). Деталі рішень — у `design.md` кожної зміни.

Попередня зміна
[`restructure-monorepo-frontend`](../../openspec/changes/archive/2026-06-12-restructure-monorepo-frontend/)
заархівована 2026-06-12 — **end-to-end запуск підтверджено** користувачем
(стек піднявся, домени `sync.loc`/`sync.dev` і HMR працюють). 4 нові
capability-специфікації злиті в `openspec/specs/` (`monorepo-layout`,
`frontend-app`, `container-orchestration`, `workspace-conventions`) і є
канонічними.

Підсумок результату (канонічні деталі — у `systemPatterns.md`/`techContext.md`/
`decisinLog.md` → D-012):

- **Монорепо:** бекенд у `api/` (пакет `app`, переїхав із `src/`, ~90
  імпортів), фронт у `front/` (Vue 3 + Vite + TS, `vue-router`, Pinia,
  `fetch`-клієнт). Docker / кореневий `Makefile` / `docs/` / `openspec/` —
  спільні на корені. Дворівневі інструкції агентів (кореневі роутери +
  per-folder `AGENTS.md`/`CLAUDE.md` з легкими вказівниками).
- **Env:** `app/config.py` вантажить env абсолютними шляхами, пріоритет
  `api/.env.template` → `<root>/.env` → `api/.env`.
- **Host-порти (конвенція, продукт 33):** api `10331`, front `10332`,
  db `11331` (схема `TT AA S`; скіл `preferred-docker-images`).
- **Dev:** `docker compose up` (hot-reload обох сервісів) або host-run
  (`make dev`/`make front-dev` + db у docker); доступ через host-nginx
  (`docker/nginx.loc.conf`) на двох доменах. Гайд —
  [`docs/technical/dev-environment.md`](../technical/dev-environment.md).

Доменна логіка, моделі та схема БД не змінювалися (alembic head
`ef2c7288bbb0`). **Незакомічене:** уся реалізація лежить у робочому дереві —
коміт за рішенням користувача.

Попередня зміна
[`add-rest-api`](../../openspec/changes/archive/2026-06-12-add-rest-api/)
заархівована 2026-06-12: REST API на FastAPI підтверджено робочим
(сервер стартує через `run_api.py`/`make serve`, ручний smoke-test
пройдено). Її 5 capability-специфікацій злиті в `openspec/specs/`
(`api-auth`, `api-jobs`, `api-sync-status`, `api-sync-triggers`,
`api-tc-projects-management`) і є канонічними.

Під час доведення API до робочого стану (сесія 2026-06-12) додатково:

- **CLI-модуль `app/cli/`** з авто-реєстрацією команд (за зразком
  `dom-ex.bot`); перша команда — `add_user` (заводить `api_users` із
  bcrypt-хешем через `APIUserDAO.create_user`). Запуск:
  `python -m app.cli add_user` або `make add-user`. Це знімає попередню
  залежність від ручного `INSERT` першого користувача.
- **Хешування паролів переведено з `passlib` на прямий `bcrypt`**
  (`app/api/auth.py`) — `passlib` 1.7.4 несумісний із `bcrypt` 5.x на
  Python 3.14 (`decisinLog.md` → D-011). Формат хешу `$2b$` збережено,
  логін сумісний.
- **Python запінено на 3.14** через `.python-version` (узгоджено з
  `dom-ex.bot`); `requires-python` лишається `>=3.12,<4.0`.
- **`Makefile`** з шорткатами поверх `uv run`: `serve`, `dev`, `cli`,
  `add-user`, `sync`.

## Як це вписується в roadmap

`add-rest-api` — завершений етап 1 траєкторії з
[`projectbrief.md`](projectbrief.md). Наступні етапи (автоматичний
планувальник, власний трекер замість TimeCamp, multi-user масштаб) на
поточний код не впливають, але мотивували multi-user-ready вибори в
`decisinLog.md` → D-009. Незакомічена правка `main.ipynb` (період
`2026-04-08 .. 2026-04-13`) відображає експлуатаційний запуск, не нову
розробку.

## Нещодавні зміни (за git log)

- `bbb67bd` — оновлення залежностей та адаптація тасків.
- `6cc9094` — фікс типу колонки `created_at` для `jr_worklogs` (DateTime).
- `e94bed8` — реалізація створення worklog-ів у `Jira` через `Tempo`.
- `0384620` — додано стадію `before_create` для `WorllogSyncTask`.
- `eda6333` — основний сервіс `create_task_for_sync` + рефакторинг таблиць.

Ці зміни вже відображені в коді й моделях — окремих міграцій для них додавати
не потрібно (остання міграція — `b4117e0c3dd4`, 2024-10-02).

## Активні відкриті питання

- **Сценарій оновлення worklog-ів.** Статуси `pre_update/update/updated` в
  `StatusTaskEnum` зарезервовані, але не використовуються. Активацію винесено в
  майбутню зміну **`add-worklog-update-flow`** (round-trip update/delete у Tempo
  для вже-`synced` блоків календаря) — див. `decisinLog.md` → D-016.
- **Назва `worllog_sync_task.py`.** Файл і клас містять одрук (`worllog` замість
  `worklog`). Перейменування зачепить імпорти — поки не виправлено
  (`decisinLog.md` → D-008).

## Найближчі кроки (як орієнтир для агентів)

1. Перед будь-якою правкою — прочитати всі файли в `docs/memory-bank/`.
2. Для нових міграцій — `alembic revision --autogenerate` після правки моделей
   (див. `techContext.md`).
3. Якщо змінюється логіка `BaseDAO._sync` — пам'ятати, що вона **видаляє**
   моделі, відсутні у DTO-списку (див. `systemPatterns.md`).

## Що ще не покрите Memory Bank

- Немає документації для веб-інтерфейсу/API (бо їх і не існує).
- Тестове покриття відсутнє; рішення про фреймворк тестів не прийняте.
