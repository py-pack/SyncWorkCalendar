## 1. Backend — схема та DAO

- [x] 1.1 Додати схеми відповіді в `api/app/api/schemas/sync_status.py`:
  `TCEntryItem` (`id, description, start_at, end_at, tc_project_id,
  tc_project_name, issue_key, is_synced`) і обгортку `TCEntriesResponse`
  (`items: list[TCEntryItem]`, `total: int`).
- [x] 1.2 Додати метод у `api/app/dao/tc_entries_dao.py`
  (напр. `list_with_sync_state`): `SELECT` `tc_entries` ⋈ `tc_projects` (назва) ⋈
  `worklog_sync_tasks` (`LEFT JOIN ON source_id = tc_entries.id AND worker_key =
  :worker_key`); похідний `is_synced = wst.status IN (created, updated)`; резолв
  `issue_key` (`meta.task` → `tc_project.issue_key`); фільтр періоду за
  `start_at`; фільтр `synced` (`all|synced|unsynced`); сортування `start_at DESC`;
  `limit`/`offset`; окремий `COUNT` для `total`.

## 2. Backend — ендпоінт

- [x] 2.1 Додати `GET /tc-entries` (у `routers/sync_status.py` або новий
  `routers/tc_entries.py`, зареєструвати в `app/api/app.py`/`routers/__init__.py`
  за наявним патерном): query `start`/`end` (дефолт — поточний місяць),
  `synced` (`Literal["all","synced","unsynced"] = "all"`), `limit` (дефолт 50,
  кап 200), `offset` (дефолт 0); `worker_key` із `get_current_user`.
- [x] 2.2 Валідація періоду `start <= end` → `400` (переюз `_period_or_400`).
- [x] 2.3 Звірити, що `GET /tc-entries/untracked` лишився без змін.

## 3. Backend — перевірка контракту

- [x] 3.1 Прогнати сервер, перевірити OpenAPI (`/docs`) на новий ендпоінт і шейп.
- [x] 3.2 Smoke-перевірка наживо: дефолтний період + пагінація; `synced=synced`/
  `unsynced`; `total` незалежний від `limit`/`offset`; scope по `worker_key`;
  `start > end` → 400; 401 без токена.

## 4. Frontend — типи та клієнт

- [x] 4.1 `front/src/api/types.ts`: тип `TCEntry` (рядок списку з `is_synced`,
  `issue_key`) і `TCEntriesResponse` (`{ items, total }`); тип фільтра
  `TCSyncFilter = 'all' | 'synced' | 'unsynced'`.
- [x] 4.2 `front/src/api/client.ts`: метод `tcEntries({ start, end, synced,
  limit, offset })` → `GET /tc-entries`.
- [x] 4.3 `front/src/lib/period.ts`: хелпери швидких шаблонів періоду (останній
  тиждень, останній місяць, цей місяць, попередній місяць) — **один спільний
  набір**, що переюзовується і picker'ом перегляду, і попапом синку (D6).

## 5. Frontend — стор

- [x] 5.1 `front/src/stores/tables.ts`: додати стан екрана TimeCamp (period
  перегляду, `syncFilter`, `page`/`offset`, `total`) і `loadTcEntries()` (читає з
  БД через `api.tcEntries`); прибрати використання `loadUntracked`/
  `autoSyncEntries` на цьому екрані.
- [x] 5.2 Додати дію синку через попап: `syncTcEntries(period)` →
  `POST /sync/timecamp/entries` → перезавантаження поточної сторінки `loadTcEntries`.
- [x] 5.3 Прибрати/деактивувати `autoSyncEntries`-виклик (лишити метод, якщо
  потрібен деінде, але екран TimeCamp його не викликає).

## 6. Frontend — попап синку

- [x] 6.1 Новий компонент попапа синку (патерн `Sheet`, як у
  `components/projects/SyncSettingsModal.vue`): поля `start`/`end` + кнопки
  швидких шаблонів; кнопки «Скасувати»/«Синхронізувати» зі станом виконання та
  помилкою.

## 7. Frontend — екран

- [x] 7.1 Переписати `front/src/views/TimeCampView.vue` на `DataPage`:
  `#actions` — кнопка синку (відкриває попап); `#toolbar` — period picker
  перегляду (зі спільними швидкими шаблонами з 4.3) + фільтр-чипи
  (`усі|синхронізовані|не синхронізовані`); тіло — `DataTable` (опис, проект,
  дата, тривалість, стан синку) + блок пагінації.
- [x] 7.2 Показати стан синку рядка (бейдж за `is_synced`); прибрати показ лише
  незіставлених і вимкнену кнопку «Зіставити».
- [x] 7.3 На `onMounted` — лише `loadTcEntries()` (жодного авто-синку).
- [x] 7.4 i18n (UK+EN): заголовки фільтра, підписи шаблонів періоду, попап синку,
  пагінація.

## 8. Перевірка

- [x] 8.1 `npm run build` (`vue-tsc --noEmit` + `vite build`) — чисто.
- [x] 8.2 Браузерний QA наживо: вибір періоду, пагінація, перемикання фільтра,
  попап синку (шаблони + синк за період), відсутність авто-синку при відкритті.
  (Підтверджено користувачем 2026-06-23 — «все працює майже як очікував».)
- [x] 8.3 `openspec validate rework-timecamp-entries-screen --strict` — OK.

## 9. UI-рефінмент за фідбеком (D9)

- [x] 9.1 Новий компактний `components/data/PeriodPicker.vue`: кнопка (іконка
  календаря + підпис діапазону / назва активного шаблону) → dropdown зі швидкими
  шаблонами (`PERIOD_PRESETS`) + ручні `start`/`end`; click-outside + Esc (патерн
  `Menu.vue`); `v-model` (`Period`). Без зовнішньої бібліотеки.
- [x] 9.2 Переюз `PeriodPicker` у `SyncEntriesModal.vue` (замість двох date-інпутів
  + ряду кнопок-пресетів).
- [x] 9.3 `TimeCampView.vue` тулбар: `PeriodPicker` + `Segmented` (фільтр стану
  синку, як на «Проектах»), **усі контроли зліва**; прибрати chip-кнопки і
  date-інпути з тулбара.
- [x] 9.4 `TimeCampView.vue` таблиця: **окрема колонка «Задача»** (`issue_key`
  key-pill); стан синку — **компактна іконка** (зелена галка / тьмяний прочерк) з
  `title`; прибрати інлайн key-pill з опису й текстовий бейдж.
- [x] 9.5 CSS (`data.css`): `.tcpp*` (поповер періоду), `.tcst*` (іконка стану);
  прибрати непотрібні `.tcbar*`/`.tcsync__dates`/`.tcsync__presets`. i18n за потреби
  (`tcsync_period`).
- [x] 9.6 `npm run build` чисто + `openspec validate --strict` OK.

## 10. Уніфікація стану синку + колонки + формат дати (D10/D11)

- [x] 10.1 `/timecamp` таблиця: порядок колонок **Проект → Задача → Опис → Дата →
  Час → Стан синку**; дата у форматі `дд.мм.рррр` (новий `lib/format.ts → fmtDate`).
- [x] 10.2 Спільні компоненти `components/data/SyncState.vue` (крапка + підпис
  `Synced`/`Not synced`) і `components/data/SyncFilter.vue` (`Segmented`
  `All|Synced|Not synced`, канонічний `SyncTri`); підписи англійською в обох
  локалях (захардкоджено).
- [x] 10.3 Перевести `/timecamp`, `/projects/timecamp`, `/projects/jira` на
  `SyncState`/`SyncFilter`; `tcActive`/`jrActive` → `SyncTri`; прибрати локальні
  `.tct__state`/`.tcst` стилі і per-екранні `Segmented`-опції.
- [x] 10.4 Зафіксувати патерн «єдина мова синку» в Memory Bank
  (`systemPatterns.md`) + auto-memory, щоб переюзовувалось надалі.
- [x] 10.5 `npm run build` чисто + `openspec validate --strict` OK.
