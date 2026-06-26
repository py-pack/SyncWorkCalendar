## Context

Екран `/journal` (`frontend-sync-journal`) — браузер таблиці `api_jobs` (журнал
кожного виклику синку: `running → needs_verification → verified` / `failed`).
Бек уже надає повний контракт `GET /api-jobs` (фільтри `status`/`trigger_name`/
`start`/`end`, пагінація `limit`/`offset` + `total`), `GET /api-jobs/{id}` і
`POST /api-jobs/{id}/verify` (capability `api-jobs`).

Поточний стан зламано: усі три ендпоінти роблять
`APIJobSummary/Detail.model_validate(<ORM>)`. ORM-поле `APIJob.status` — член
enum `APIJobStatusEnum`; схема оголошує `status: APIJobStatusLiteral`
(`Literal[str]`). Pydantic v2 з `from_attributes=True` не коерсить enum-member у
`.value` проти `Literal`, тож кидає `ValidationError` на кожному рядку → 500
(підтверджено в логах контейнера: `literal_error … input_type=APIJobStatusEnum`).
Поки `api_jobs` була порожня, список повертав `[]` і не падав; Celery
beat/worker наповнив таблицю (306 рядків `needs_verification`) — і екран ліг.

Сусідній `GET /worklog-sync-tasks` тієї ж пастки уникає, бо роутер будує
елементи **вручну**: `WorklogSyncTaskItem(status=t.status.value, …)`.

Фронт при цьому відстає від спільного патерну дані-екранів
(`rework-timecamp-entries-screen` → `/jira` → `/tempo`): немає `PeriodPicker`,
немає пагінації, дати форматуються сирими `.slice()`, фільтр статусу — локальні
«chips».

## Goals / Non-Goals

**Goals:**
- Усунути 500 на всіх трьох ендпоінтах `/api-jobs/**` одним фіксом серіалізації.
- Привести `/journal` до спільного формату: `PeriodPicker` за `started_at`,
  серверна пагінація, єдиний `fmtDate` (`дд.мм.рррр`), спільний `FilterSelect`.
- Зберегти наявну поведінку: деталі (`payload`/`result`/`error`), `verify`,
  лічильник `needs_verification` у навігації.

**Non-Goals:**
- Жодних змін у моделі/схемі БД, **без alembic** (head `69dde0d17ff2`).
- Жодних нових ендпоінтів — бек-контракт `GET /api-jobs` уже достатній.
- Бінарна «мова синку» (`SyncState`/`SyncFilter`/`SyncTri`) тут **не**
  застосовується (статус job-а — 4-станова машина, не synced/not-synced).
- TTL/cleanup старих `needs_verification` job-ів — окрема майбутня
  `add-api-jobs-cleanup` (лічильник навбейджа може показувати велике число — це
  очікувано і поза скоупом).
- Скасування/повтор job-а, bulk-verify — поза скоупом.

## Decisions

**D1. Фікс серіалізації — нормалізація на рівні схеми (`field_validator`),
а не ручна побудова в роутері.**
У схему `APIJobSummary` додаємо `@field_validator("status", mode="before")`, що
повертає `v.value if isinstance(v, enum.Enum) else v`. `APIJobDetail`
успадковує її. Чому так, а не «як WST» (ручний `Item(status=t.status.value)`):
журнал використовує `model_validate(<ORM>)` у **трьох** місцях (список, деталі,
verify) — валідатор лагодить усі одразу й лишає роутер компактним. Тип лишаємо
`Literal[str]` (чистий OpenAPI-енум зі строкових значень для фронта).
*Альтернатива:* типізувати поле як сам `APIJobStatusEnum` + `use_enum_values=True`
— відкинуто: змінює OpenAPI-репрезентацію і впливає на всі шляхи побудови.

**D2. Період — `PeriodPicker` за `started_at`, дефолт «цей місяць».**
Бек уже фільтрує `started_at BETWEEN start AND end`. Беремо спільний
`PeriodPicker` і `defaultReviewPeriod()` (як `/timecamp`/`/tempo`). Місяць —
розумний дефолт для активного логу (job-и створюються щодня). *Альтернатива:*
«поточний рік» (як `/jira`) — відкинуто: журнал — це свіжа активність, не архів
задач; пресети все одно дають ширший вибір.

**D3. Серверна пагінація — наявні `limit`/`offset`/`total`.**
Стор тримає `offset`/`total`/`pageSize`; зміна періоду чи фільтра скидає
`offset` у 0 (той самий патерн, що `loadTcEntries`/`loadJrIssues`). Жодних
змін на беку.

**D4. Дати — лише через `fmtDate` (`дд.мм.рррр`), час — окремо.**
Прибираємо всі `.slice(5,16)`/`.slice(0,19)`/`.slice(11,19)`. У таблиці колонка
«Старт» = `fmtDate(started_at)` + `HH:MM`; у бічній панелі — те саме для
`started_at`/`finished_at`/`verified_at`. Формат дати ідентичний іншим екранам.

**D5. Фільтр — спільний `FilterSelect` (статус + `trigger_name`), не «chips».**
Статус — `FilterSelect` з опціями `усі / running / needs_verification /
verified / failed` (узгоджено з контролами `/jira`). Додаємо другий
`FilterSelect` за `trigger_name` (бек уже приймає; список тригерів — статичний
з відомих імен синку або з фронт-константи). Прибираємо локальні `.cal__chips`
з `JournalView`. Бінарний `SyncFilter` свідомо **не** застосовуємо (D у
Non-Goals). *Альтернатива:* лишити «chips» — відкинуто заради єдиного вигляду
тулбарів.

**D6. «Кнопка синку» = «Оновити» (re-read з БД).**
Журнал — сам лог синків; зовнішнього джерела для нього немає. Тож кнопка дій
лишається `SyncBtn`-«Оновити» (повторний `load()`), що відповідає принципу
«фронт показує те, що в БД». Авто-`load` на `onMounted` лишається (це читання з
БД, а не зовнішній синк — дозволено).

## Risks / Trade-offs

- **[Лічильник навбейджа показує велике число (306+)]** → Очікувано: job-и
  накопичуються, бо їх ніхто не verify-ить. Поза скоупом; адресується окремою
  `add-api-jobs-cleanup`. Фікс лише розблоковує лічильник (зараз він 500-иться).
- **[Великий період × багато тригерів → багато рядків]** → Серверна пагінація
  (D3) і дефолт «цей місяць» (D2) тримають вибірку обмеженою; `limit` кап 500 на
  беку.
- **[`trigger_name`-фільтр на статичному списку може розійтися з реальними
  іменами]** → Імена тригерів стабільні (константи беку, напр.
  `sync.timecamp.entries`); за потреби список легко звести з фактичних значень
  пізніше. Низький ризик, не блокує.
- **[Регрес 500 у майбутньому]** → Пін у спеці `api-jobs` (status серіалізується
  як рядок і не падає за наявності рядків) фіксує контракт як регрес-гард;
  бажано покрити smoke-перевіркою на непорожній таблиці.
