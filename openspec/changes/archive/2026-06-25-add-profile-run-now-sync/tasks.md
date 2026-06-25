## 1. API-клієнт (`front/src/api/`)

- [x] 1.1 Перевірити наявні методи тригерів у `api/client.ts` (уже є:
  `syncTcProjects`, `syncTcEntries`, `syncJrProjects`, `syncJrIssuesAll`,
  `syncJrWorklogs`, `syncWstPush` = `/sync/worklog-tasks/push-to-tempo`)
- [x] 1.2 Додати **єдиний відсутній** метод `reconcileLinks(period: Period)` →
  `POST /sync/reconcile-links` (повертає `202 {job_id, status:"queued"}`); за
  потреби розширити тип результату, щоб розрізняти `result`-дельту і `queued`
- [x] 1.3 Перевірити/уточнити тип `SyncTriggerResult` у `api/types.ts` —
  має покривати обидві форми відповіді (синхронну з `result` і enqueue з `status`)

## 2. Дескриптори дій і спільний попап (`front/src/components/profile/`)

- [x] 2.1 Описати мапу `RUN_ACTIONS` (по ключу `keyof SyncPrefs`): заголовок/
  підказка/іконка (i18n-ключі) + `run(period)` — виконавець, що кличе
  відповідні `api.*` (без релоаду таблиць інших екранів, D5)
- [x] 2.2 У виконавцях TimeCamp/Jira **дзеркалити крон** (D3): спершу
  `api.syncTcProjects()` / `api.syncJrProjects()`, потім
  `api.syncTcEntries(period)` / `api.syncJrIssuesAll(period)`; помилка синку
  проектів зупиняє дію до запиту даних
- [x] 2.3 Створити `components/profile/RunSyncModal.vue` за зразком
  `SyncEntriesModal.vue`/`PullWorklogsModal.vue`: `Sheet` + `PeriodPicker`
  (дефолт `syncPeriod()` із `lib/period.ts`) + `Field` + `Btn` + `Spinner`;
  prop — активний ключ дії, бере метадані з `RUN_ACTIONS`
- [x] 2.4 Реалізувати дві гілки результату (D1/D2): синхронні дії показують
  **дельту** в попапі; `auto_linking` (відповідь `202`) показує «поставлено в
  чергу — див. Журнал синку» і закриває попап
- [x] 2.5 Обробка помилок: ловити `ApiError`, показувати `detail` без закриття
  попапа (зокрема `400 "user has no worker_key configured"`, D6)

## 3. Кнопки в `SyncPrefsToggles.vue`

- [x] 3.1 Додати в кожен рядок `.sprefs__row` кнопку **«Запустити зараз»**
  (іконка `sync`/`play`) поряд із `Toggle`
- [x] 3.2 Клік відкриває `RunSyncModal` з ключем рядка; тримати локальний стан
  `openKey: keyof SyncPrefs | null`
- [x] 3.3 (UX, опц., D6) Дизейблити кнопку для worker_key-залежних дій
  (`auto_tempo_pull`/`auto_linking`/`auto_push_tempo`), якщо
  `auth.currentUser?.worker_key` порожній, із підказкою-tooltip

## 4. i18n (`front/src/i18n/strings.ts`)

- [x] 4.1 Додати ключі (UK+EN): підпис кнопки «Запустити зараз», заголовки/
  підказки попапа для кожної з 5 дій, тексти результату («Готово: …»,
  «Поставлено в чергу — див. Журнал»)
- [x] 4.2 Перевірити, що `StringKey`-типи не ламають збірку (нові ключі додані в
  обидві локалі)

## 5. Стилі (`front/src/styles/data.css`)

- [x] 5.1 За потреби — дрібні правки `.sprefs__row` під додаткову кнопку
  (вирівнювання), реюз наявних `.tcsync*` для тіла попапа; без нового макета

## 6. Валідація і QA

- [x] 6.1 `openspec validate add-profile-run-now-sync --strict` — OK
- [x] 6.2 `npm run build` (`vue-tsc` + `vite`) — чисто
- [ ] 6.3 Браузерний QA (на користувача): кнопка в кожному рядку → попап →
  період → дія; перевірити синхронну дельту (TimeCamp/Jira/Tempo/push),
  enqueue-повідомлення (linking), помилку без `worker_key`
