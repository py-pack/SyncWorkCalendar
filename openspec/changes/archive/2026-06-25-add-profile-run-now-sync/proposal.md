## Why

Тумблери `sync_prefs` на закладці «Синхронізації» лише вмикають/вимикають
**плановий** (крон/`beat`) автосинк — користувач не може запустити ту саму дію
негайно за обраний період. Щоб перевірити налаштування чи доганяти дані «тут і
зараз», доводиться йти на окремі екрани (`/timecamp`, `/jira`, `/tempo`) і шукати
відповідний попап. Це додає одну кнопку «Запустити зараз» напроти кожного
тумблера — ручний еквівалент кожної планової команди в одному місці.

## What Changes

- Напроти **кожного** з 5 тумблерів `sync_prefs` на закладці «Синхронізації»
  зʼявляється кнопка «Запустити зараз».
- Клік відкриває **спільний** попап із `PeriodPicker` (дефолт — «цей місяць»), де
  користувач обирає період і запускає відповідну дію негайно.
- Кожна команда мапиться на **наявний** sync-тригер (нових ендпоінтів не треба):
  - `auto_timecamp_pull` → `POST /sync/timecamp/projects` + `POST /sync/timecamp/entries`
  - `auto_jira_pull` → `POST /sync/jira/projects` + `POST /sync/jira/issues-all`
  - `auto_tempo_pull` → `POST /sync/jira/worklogs`
  - `auto_linking` → `POST /sync/reconcile-links`
  - `auto_push_tempo` → `POST /sync/worklog-tasks/push-to-tempo`
- Виконання **синхронне** (дзеркалить наявні попапи `SyncEntriesModal`/
  `PullWorklogsModal`): спінер до завершення, далі дельта або помилка в попапі.
  Виняток — `auto_linking` (реконсиляція), що за природою лише ставиться в чергу
  (бек завжди `202`); для неї попап показує «поставлено в чергу, див. Журнал».
- Команди TimeCamp/Jira **дзеркалять крон**: спершу синк проектів (без періоду),
  потім дані за обраний період.
- Дії з worker_key-залежністю (`auto_tempo_pull`, `auto_linking`,
  `auto_push_tempo`) без налаштованого `worker_key` показують зрозумілу помилку
  (бек віддає `400 "user has no worker_key configured"`).

## Capabilities

### New Capabilities
<!-- Немає нових capability — фіча розширює наявний екран «Профіль». -->

### Modified Capabilities

- `frontend-profile`: ADDED-вимога «Запуск синку «зараз» із закладки
  «Синхронізації»» — кнопка напроти кожного тумблера + попап вибору періоду, що
  викликає відповідний наявний sync-тригер.

## Impact

- **Frontend (`front/`):**
  - `components/profile/SyncPrefsToggles.vue` — кнопка «Запустити зараз» у кожному
    рядку; відкриття спільного попапа.
  - Новий `components/profile/RunSyncModal.vue` — спільний попап (`Sheet` +
    `PeriodPicker`), параметризований дією (за зразком `SyncEntriesModal`).
  - `stores/auth.ts` або `stores/tables.ts` — стор-дії на кожен тригер (реюз
    наявних `syncTcEntries`/`syncJrWorklogs`, де можливо; нові для
    `issues-all`/`reconcile`/`push-to-tempo`/`projects`).
  - `api/client.ts` — методи для тригерів, яких ще немає в клієнті.
  - `i18n/strings.ts` — нові ключі (UK+EN).
  - CSS у `styles/data.css` (реюз `.sprefs*`/`.tcsync*`).
- **Backend:** змін **немає** — усі тригери вже існують і канонічні в
  `openspec/specs/api-sync-triggers`. Контракт не змінюється.
- **Без alembic-міграції** (head лишається `69dde0d17ff2`).
