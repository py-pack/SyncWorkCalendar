## 1. Backend — фікс серіалізації (500)

- [x] 1.1 У `api/app/api/schemas/api_jobs.py` додати `@field_validator("status", mode="before")` в `APIJobSummary`, що повертає `v.value if isinstance(v, enum.Enum) else v` (успадковується `APIJobDetail`); імпортувати `enum` і `field_validator`.
- [x] 1.2 Перевірити наживо на непорожній таблиці: `GET /api-jobs`, `GET /api-jobs?status=needs_verification&limit=1`, `GET /api-jobs/{id}` → `200 OK`, `status` — рядок; `POST /api-jobs/{id}/verify` → `200`. *(Список/навбейдж/деталі — `200`, `status`='needs_verification' (str), 306 рядків; `verify` — той самий доведений шлях `model_validate`, наживо не запускали, щоб не мутувати реальні рядки.)*
- [x] 1.3 Підтвердити, що моделі/БД не змінювались — alembic head лишається `69dde0d17ff2` (без нової ревізії).

## 2. Frontend — клієнт і стор

- [x] 2.1 У `front/src/api/client.ts` розширити `apiJobs(params)` опційними `start`/`end` (ISO date) поверх наявних `status`/`trigger_name`/`limit`/`offset`.
- [x] 2.2 У `front/src/stores/journal.ts` додати стан: `period` (дефолт `defaultReviewPeriod()`), `statusFilter`, `triggerFilter`, `offset`, `total`, `pageSize`; `load()` передає всі параметри; сетери періоду/фільтрів скидають `offset` у 0 і перезавантажують.
- [x] 2.3 Зберегти `needsCount`/`refreshNeedsCount`, `open`/`close`, `verify` без зміни поведінки (verify оновлює рядок локально).

## 3. Frontend — екран `/journal`

- [x] 3.1 У `views/JournalView.vue` додати в тулбар спільний `PeriodPicker` (за `started_at`) і два `FilterSelect` (статус: `усі/running/needs_verification/verified/failed`; `trigger_name`); прибрати локальні `.cal__chips`.
- [x] 3.2 Додати серверну пагінацію (контрол сторінок поверх `offset`/`total`/`pageSize`), як на `/timecamp`/`/jira`/`/tempo`.
- [x] 3.3 Замінити сирі `.slice()` дат на `fmtDate` (`дд.мм.рррр`) + час (`HH:MM`) у колонці «Старт» і в усіх датах бічної панелі (`started_at`/`finished_at`/`verified_at`).
- [x] 3.4 Лишити кнопку «Оновити» (`SyncBtn` → `store.load()`), деталі (`payload`/`result`/`error`) і крок `verify` без зміни.

## 4. i18n та стилі

- [x] 4.1 Додати/узгодити i18n-ключі (UK+EN) для лейблів фільтра статусу/тригера та пагінації; прибрати мертві ключі від «chips», якщо лишаються невикористані.
- [x] 4.2 CSS — переюзати наявні класи тулбара/пагінації дані-екранів у `styles/data.css`; прибрати локальні стилі «chips», якщо більше не потрібні. *(Тулбар → `.pipe`/`.jrbar`, пагінація → `.tcpage`; `.cal__chips`/`.chip` лишаються в `data.css` — їх використовує `CalendarFilters.vue`.)*

## 5. Перевірка

- [x] 5.1 `cd front && npm run build` (`vue-tsc --noEmit` + `vite build`) — чисто.
- [x] 5.2 `openspec validate rework-journal-screen --strict` — OK.
- [ ] 5.3 Браузерний QA `/journal` (на користувача): список вантажиться без 500, період/фільтри/пагінація працюють, дати у `дд.мм.рррр`, деталі й verify працюють, навбейдж `needs_verification` коректний.
