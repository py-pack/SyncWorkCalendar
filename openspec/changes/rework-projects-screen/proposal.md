## Why

Екран **«Проекти → TimeCamp»** при відкритті б'є **6 запитів** замість одного:
`ProjectsView.onMounted` викликає `loadProjects()` (GET `/tc-projects?start&end` +
GET `/jr-projects`) **і** `autoSyncProjects()` (POST `/sync/timecamp/projects` +
POST `/sync/jira/projects` + повторний `loadProjects()`). Авто-синк при кожному
відкритті — марнотратство і ризик. Додатково: TimeCamp-проекти насправді **дерево**
(`tc_projects.parent_id`), але рендеряться плоским списком; поле `color` не
використовується; інлайн-тогл `is_sync` дозволяє **випадково** вимкнути синк; у
маппінгу видно лише сирий `issue_key` без назви Jira-задачі; а date-фільтр
(`start`/`end`) у `/tc-projects` існує **тільки** заради per-period `entries_count`,
хоча проекти не мають залежати від періоду.

## What Changes

- **BREAKING (API):** `GET /tc-projects` втрачає параметри `start`/`end` і поле
  `entries_count`. Натомість у відповідь додаються `parent_id`, `color`,
  `issue_name` (резолв назви Jira-задачі через LEFT JOIN `jr_issues` за
  `issue_key`) і `issue_active` (чи задача не в «done»-статусі). Зʼявляється
  фільтр `active = active|inactive|all` (за `is_archived`, дефолт `all`).
- **API:** `GET /jr-issues` отримує пошук `q` (case-insensitive по `key`/`name`) і
  `limit` (дефолт 10) для select-а з пошуком; у відповідь додається похідний
  прапор `active` (статус не в «done»-сеті).
- **Frontend:** під-вʼюха **TimeCamp-проекти** стає **деревом** (`parent_id`) з
  кольоровим акцентом (`color`); архівні проекти — сірі/напівпрозорі; **фільтр за
  станом синку** (`is_sync`: усі / у синку / не в синку) і **швидке поле пошуку**
  по локальних даних — обидва клієнтські (без re-fetch). Тег змапованої задачі —
  **одразу біля назви** проекту.
- **Frontend:** інлайн-тогл `is_sync` **прибирається**. Рядок показує індикатор
  стану синку («синхронізується / ні»), маповану задачу кольоровим тегом
  (`issue_key` + `issue_name`, тінт `color`, тьмяна якщо `issue_active=false`) і
  кнопку налаштувань; **подвійний клік** по рядку теж відкриває налаштування.
- **Frontend (новий попап):** модалка налаштувань синку — тогл «увімкнути синк» +
  **select задачі з пошуком** (вводиш → `GET /jr-issues?q=&limit=10`, до 10
  результатів, закриті задачі тьмяні). **Save заблоковано**, поки синк увімкнено,
  а задачу не обрано. Save → `PATCH /tc-projects/{id} {is_sync, issue_key}`.
  Вимкнення синку зберігає наявний `issue_key` (просто перестає синкати) — Save
  дозволено.
- **Frontend:** авто-синк при відкритті **видаляється повністю**; синк проектів
  стає **окремою явною кнопкою** в шапці («Синхронізувати проекти» →
  POST `/sync/timecamp/projects` + POST `/sync/jira/projects` + reload), яка
  ніколи не запускається сама.
- **Frontend (лінива загрузка):** кожна під-вʼюха вантажить **власні** дані одним
  запитом при відкритті — `/projects/timecamp` робить **лише `GET /tc-projects`**;
  `GET /jr-projects` тягнеться **тільки** при переході на вкладку Jira (а не
  одразу). Відкриття сторінки: з **6 запитів → 1** (`GET /tc-projects`).

## Capabilities

### New Capabilities

<!-- Нових capability немає — усе вкладається в існуючі. -->

### Modified Capabilities

- `api-tc-projects-management`: додаємо вимогу на `GET /tc-projects` (раніше
  capability документувала лише PATCH) — без date-фільтра/`entries_count`, з
  деревними полями (`parent_id`, `color`), резолвом маппінгу (`issue_name`,
  `issue_active`) і фільтром `active`.
- `api-jira-read`: розширюємо `GET /jr-issues` параметрами пошуку `q`/`limit` і
  похідним прапором `active` для select-а з пошуком.
- `frontend-data-tables`: переписуємо вимогу «Екран «Проекти»» (під-вʼюха
  TimeCamp) — дерево замість списку, кольори, попап налаштувань замість інлайн-тогла,
  прибраний авто-синк, окрема кнопка синку, мапована задача з назвою/кольором.

## Impact

- **Backend:** `api/app/api/routers/tc_projects.py`,
  `api/app/api/schemas/tc_projects.py`, `api/app/api/routers/jr_issues.py`,
  `api/app/api/schemas/jr_issues.py`, `api/app/dao/jr_issues_dao.py`
  (`list_filtered` + пошук), новий невеликий хелпер «done-status».
  **Без alembic-міграції** — `parent_id`/`color`/`issue_key`/`status` уже є в
  моделях; sync-рушій не зачіпається.
- **Frontend:** `front/src/views/projects/TcProjects.vue`,
  `front/src/views/ProjectsView.vue`, `front/src/stores/tables.ts`,
  `front/src/api/client.ts`, `front/src/api/types.ts`,
  `front/src/i18n/strings.ts`; **нова** модалка налаштувань синку та хелпер
  побудови дерева; нові стилі дерева/тега.
- **Контракт API (BREAKING для фронту):** споживач `GET /tc-projects` має
  перейти зі схеми `{..., entries_count}` на `{..., parent_id, color, issue_name,
  issue_active}` без `start`/`end`. Інших зовнішніх споживачів немає (єдиний
  клієнт — цей фронт).
- **Поза скоупом:** під-вʼюха Jira-проектів (лишається з власним `is_watched`),
  sync-рушій, схема БД.
