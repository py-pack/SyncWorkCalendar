## Why

Екран **«Журнал синку»** (`/journal`) зараз повністю зламаний: будь-який
`GET /api-jobs` (включно з `?status=needs_verification&limit=1` для лічильника
в навігації) повертає **500 Internal Server Error**. Причина — серіалізаційний
баг: усі три ендпоінти (`GET /api-jobs`, `GET /api-jobs/{id}`,
`POST /api-jobs/{id}/verify`) роблять `APIJobSummary/Detail.model_validate(<ORM>)`,
де ORM-атрибут `APIJob.status` — це **член enum** `APIJobStatusEnum`, а схема
оголошує `status: Literal["running", …]`. Pydantic v2 із `from_attributes=True`
**не** зводить enum-member до `.value` проти `Literal[str]` і кидає
`ValidationError` на **кожному** рядку. Баг «прокинувся» лише тепер, бо Celery
beat/worker за останню добу наплодив `api_jobs`-рядки (на момент аналізу — **306**,
усі `needs_verification`); поки таблиця була порожня, список повертав `[]` і не
падав.

Окрім фікса, екран треба привести **до одного формату з рештою дані-екранів**
(`/timecamp`, `/jira`, `/tempo`): фронт показує те, що в БД; дати й статуси
рендеряться спільними засобами. Зараз `/journal` не має фільтра за періодом
(хоча в `api_jobs` є дата `started_at`), не пагінує (хоча бек уже віддає
`limit`/`offset`/`total`) і форматує дати сирими `.slice()` замість спільного
`fmtDate` (`дд.мм.рррр`).

## What Changes

- **Фікс 500 (backend):** `status` в `APIJobSummary`/`APIJobDetail` MUST
  серіалізуватися як рядкове значення enum (`.value`) — через нормалізацію на
  рівні схеми, щоб `model_validate(<ORM>)` приймав і enum-member, і рядок.
  Лагодить усі три ендпоінти одразу (список, деталі, verify) і лічильник
  навбейджа.
- **Період (frontend):** додати `PeriodPicker` за датою `started_at` (бек уже
  приймає `start`/`end`), дефолт — поточний місяць (`defaultReviewPeriod`).
- **Серверна пагінація (frontend):** використати наявні `limit`/`offset`/`total`
  з `GET /api-jobs`, як на `/timecamp`/`/jira`/`/tempo`.
- **Єдиний формат дат (frontend):** замінити сирі `.slice()` у таблиці та в
  бічній панелі деталей на спільний `fmtDate` (`дд.мм.рррр`) + час; узгодити з
  іншими екранами.
- **Уніфікований фільтр (frontend):** перевести ad-hoc «chips» фільтра статусу на
  спільний контрол `FilterSelect` (як на `/jira`) і додати фільтр за
  `trigger_name` (бек уже приймає його) — бінарна «мова синку»
  (`SyncState`/`SyncFilter`) тут **не** застосовується (статус job-а — це
  4-станова машина життєвого циклу, а не synced/not-synced).
- **Без змін:** деталі job-а (`payload`/`result`/`error` як JSON), крок
  `verify`, лічильник `needs_verification` у навігації — лишаються; кнопка
  «Оновити» (re-read з БД) лишається (зовнішнього джерела для синку в журналу
  немає — він **сам** є логом синків).

## Capabilities

### New Capabilities
<!-- Нових capability немає. -->

### Modified Capabilities
- `api-jobs`: уточнити контракт — поле `status` у відповідях `GET /api-jobs`,
  `GET /api-jobs/{id}` і `POST /api-jobs/{id}/verify` MUST серіалізуватися як
  рядкове значення (`running`/`needs_verification`/`verified`/`failed`), а
  серіалізація MUST не падати за наявності рядків (регрес-гард проти 500).
- `frontend-sync-journal`: екран «Журнал синку» отримує фільтр за періодом
  (`PeriodPicker` за `started_at`), серверну пагінацію, єдиний формат дат
  (`fmtDate`) і спільний контрол фільтра (`FilterSelect` за статусом і
  `trigger_name`).

## Impact

- **Backend (`api/`):** `app/api/schemas/api_jobs.py` (нормалізація enum→value
  для `status`). Без нових ендпоінтів, без зміни моделі/БД, **без alembic**
  (head `69dde0d17ff2`). Контракт `GET /api-jobs` (params/шейп) уже відповідає
  спеці — фіксуємо лише серіалізацію.
- **Frontend (`front/`):** `stores/journal.ts` (стан періоду/пагінації/фільтрів,
  параметри в `load`), `views/JournalView.vue` (`PeriodPicker` + `FilterSelect`
  + пагінація + `fmtDate`), `api/client.ts` (`apiJobs` — додати `start`/`end`),
  i18n (UK+EN), CSS у `data.css`. Без нових залежностей.
- **Сумісність:** виправлення розблоковує і навбейдж (`needs_verification`),
  який зараз теж 500-иться. Накопичення непідтверджених job-ів (TTL/cleanup
  старих `api_jobs`) — **поза скоупом** (майбутня `add-api-jobs-cleanup`).
