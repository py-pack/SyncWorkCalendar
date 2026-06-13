# Active Context

## Дата оновлення

2026-06-13 — **фази 1, 2 і 3 заархівовані**; код усіх у робочому дереві, не
закомічено. Фаза 2 (`add-calendar-timesheet`, read-only візуалізація, D-016)
— **реалізована, браузерний QA пройдено наживо, заархівована 2026-06-13**;
2 нові capability злиті в `openspec/specs/` і канонічні: `api-calendar`,
`frontend-calendar`. Лишився лише git-commit.

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
