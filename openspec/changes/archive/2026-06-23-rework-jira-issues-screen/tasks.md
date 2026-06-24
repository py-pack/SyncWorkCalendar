## 1. Backend — схема та DAO

- [x] 1.1 Додати обгортку відповіді `JRIssuesPage` (`items: list[JRIssueItem]`,
  `total: int`) у `api/app/api/schemas/jr_issues.py`; `JRIssueItem` лишається з
  наявними полями + похідне `active`.
- [x] 1.2 Додати метод у `api/app/dao/jr_issues_dao.py` (`list_paginated`):
  фільтри `project_id`, `status` (точний збіг), `q` (ILIKE `key`/`name`),
  період **активності** за `updated_at` (`updated_from`/`updated_to` — пост-QA
  пивот із `created_at`); сортування `updated_at` спадно (`NULL` останніми);
  `limit`/`offset`; окремий `COUNT` для `total`.
- [x] 1.3 Додати метод `distinct_statuses(db)` у
  `api/app/dao/jr_issues_dao.py` — усі distinct `jr_issues.status` (за абеткою).

## 2. Backend — ендпоінти

- [x] 2.1 Переписати `GET /jr-issues` у `api/app/api/routers/jr_issues.py`:
  query `updated_from`/`updated_to` (дефолт — поточний місяць), `project_id`,
  `status`, `q`, `limit` (дефолт 50, кап 200), `offset` (дефолт 0);
  `response_model=JRIssuesPage`. Валідація `updated_from <= updated_to` → `400`
  (переюз `period_or_400`); дефолт періоду — `current_month`.
- [x] 2.2 Переюзати/винести хелпери `_current_month`/`_period_or_400` зі
  `routers/sync_status.py` (за потреби — у спільний модуль), щоб не дублювати.
  → винесено в `api/app/api/period.py` (`current_month`/`period_or_400`);
  `sync_status.py` імпортує їх через alias.
- [x] 2.3 Додати `GET /jr-issues/statuses` (auth) → `list[str]` усіх статусів
  через `distinct_statuses`.

## 3. Backend — перевірка контракту

- [x] 3.1 Прогнати сервер, перевірити OpenAPI (`/docs`) на новий шейп
  `GET /jr-issues` і новий `GET /jr-issues/statuses`. → OpenAPI на живому
  контейнері (`:10331`, hot-reload) підтверджує: `GET /jr-issues` →
  `JRIssuesPage` з параметрами `created_from`/`created_to`/`project_id`/`status`/
  `q`/`limit`/`offset`; `GET /jr-issues/statuses` → `list[str]`.
- [x] 3.2 Smoke-перевірка наживо: дефолтний період + пагінація; фільтри
  `project_id`/`status`/`q`; `total` незалежний від `limit`/`offset`;
  `updated_from > updated_to` → 400; `GET /jr-issues/statuses`; 401 без токена. →
  **401-гейт підтверджено автоматично**; авторизовані шляхи підтверджено
  **користувачем наживо в браузері** 2026-06-23 («все працює»).

## 4. Frontend — типи та клієнт

- [x] 4.1 `front/src/api/types.ts`: `JRIssuesPage` (`{ items: JRIssue[], total:
  number }`); `JRIssue` лишається.
- [x] 4.2 `front/src/api/client.ts`: `jrIssues(...)` → `JRIssuesPage` із
  параметрами `projectId`/`q`/`status`/`createdFrom`/`createdTo`/`limit`/`offset`;
  новий `jrIssueStatuses()` → `GET /jr-issues/statuses`; новий
  `syncJrWorklogs(period)` → `POST /sync/jira/worklogs`; `syncJrProjects` лишається.
- [x] 4.3 Виправити `jrIssueSearch` у `front/src/stores/tables.ts` на читання
  `.items`. **Рішення користувача:** мапінг-select шукає серед УСІХ задач, тож
  передаємо широкий період (`createdFrom: '2000-01-01'`, `createdTo: '2999-12-31'`),
  а не дефолтний поточний місяць; задачі з `NULL created_at` у пошук не потраплять
  (відоме обмеження).

## 5. Frontend — стор

- [x] 5.1 `front/src/stores/tables.ts`: додати стан екрана Jira (`jrPeriod`
  перегляду — дефолт поточний місяць, `jrStatus`, `jrProjectFilter`, `jrQuery`,
  `jrOffset`, `jrTotal`, `jrPageSize`, `jrStatusOptions`) і `loadJrIssues()`
  (читає з БД через `api.jrIssues`); завантаження `jrProjects` (для випадайки) і
  `jrIssueStatuses` (для випадайки статусів — один раз).
- [x] 5.2 Сетери з reset пагінації: `setJrPeriod`/`setJrStatus`/`setJrProjectFilter`/
  `setJrQuery` (скидають `jrOffset` на 0 і перезавантажують), `setJrOffset`
  (пагінація).
- [x] 5.3 Дія синку через попап: `syncJrIssues(period)` →
  `api.syncJrProjects()` потім `api.syncJrWorklogs(period)` →
  перезавантаження поточної сторінки `loadJrIssues`.
- [x] 5.4 Прибрати виклик `autoSyncIssues` з екрана Jira (метод можна лишити, якщо
  потрібен деінде, але `JiraView` його не викликає); прибрати/замінити
  `loadIssues` на `loadJrIssues`. → `autoSyncIssues`/`loadIssues` видалено (немає
  інших споживачів).

## 6. Frontend — попап синку та Select

- [x] 6.1 Новий компонент `components/jira/SyncIssuesModal.vue` (патерн `Sheet`, як
  `components/timecamp/SyncEntriesModal.vue`): `PeriodPicker` + кнопки
  «Скасувати»/«Синхронізувати» зі станом виконання та помилкою; викликає
  `store.syncJrIssues(period)`.
- [x] 6.2 Невеликий переюзовний `Select`/dropdown (проект + статус) на патерні
  поповера `components/ui/Menu.vue` (click-outside + Esc), без зовнішньої
  бібліотеки; вибір проекту — з пошуком (як select задачі у `SyncSettingsModal.vue`),
  опція «усі» знімає фільтр. → `components/data/FilterSelect.vue` (`searchable`-проп).

## 7. Frontend — екран

- [x] 7.1 Переписати `front/src/views/JiraView.vue` на `DataPage`: `#actions` —
  кнопка синку (відкриває попап); `#toolbar` (усі контроли зліва) — `PeriodPicker`
  (період створення) + випадайка проекту + випадайка статусу + пошук за назвою;
  тіло — `DataTable` + блок пагінації (prev/next + позиція, як `/timecamp`).
- [x] 7.2 Колонки у порядку **проект → тип → статус → номер (`key`) → опис**;
  статус — `Badge` (тон за статусом), проект — `ProjTag`, номер — key-pill.
- [x] 7.3 На `onMounted` — лише `loadJrIssues()` (жодного авто-синку).
- [x] 7.4 i18n (UK+EN): підписи фільтрів (проект/статус/пошук), період, попап синку,
  пагінація — переюз наявних `col_*`/`period_*`/`page_*`, нові ключі за потреби.

## 8. Перевірка

- [x] 8.1 `npm run build` (`vue-tsc --noEmit` + `vite build`) — чисто (включно з
  оновленим `jrIssueSearch`).
- [x] 8.2 Браузерний QA наживо: дефолтний період, пагінація, фільтри
  (проект/статус/пошук), вибір періоду активності, попап синку (витяг задач за
  період), відсутність авто-синку при відкритті, порядок колонок. → **підтверджено
  користувачем наживо** 2026-06-23 («все працює»).
- [x] 8.3 `openspec validate rework-jira-issues-screen --strict` — OK.

## Пост-QA пивот (фідбек користувача наживо)

- **Період екрана — за `updated_at` (активність), не `created_at`** (D5): фільтр і
  сорт `GET /jr-issues` переведено на `updated_at`; query — `updated_from`/
  `updated_to`; клієнт/стор — `updatedFrom`/`updatedTo`. Семантика: «показувати те,
  з чим працювали у вікні», незалежно від дати створення. Та сама вісь — і в синку
  (`add-jira-full-issue-pull`).
- **Синк за період** на `/jira` тепер виконує **витяг задач** (`POST
  /sync/jira/issues-all`, зміна `add-jira-full-issue-pull`), а не projects+worklogs;
  одна кнопка-попап. `store.syncJrIssues` (worklog-потік) видалено.
- Дефолт екрана — поточний рік; фільтр проектів — лише `is_watched`; фікс
  `FilterSelect` (`flex: none`). Спека/`design.md` оновлені; `npm run build` чисто;
  `validate --strict` OK.
