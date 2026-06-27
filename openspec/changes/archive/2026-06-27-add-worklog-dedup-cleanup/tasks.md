## 1. Backend — пошук дублів

- [x] 1.1 `app/dao/jr_worklog_dao.py`: `find_duplicate_groups(db, worker_key,
  date_from, date_to)` — `GROUP BY (jr_issues_id, jr_worker_key, started_at,
  duration) HAVING count(*) > 1`, scoped по `worker_key`, join `jr_issues`
  (`key`/`name`), повертає групи з членами (`id`, `description`, `created_at`,
  `is_linked` через EXISTS на `WST.target_id`).
- [x] 1.2 Схеми `WorklogDuplicateMember`/`WorklogDuplicateGroup`/
  `WorklogDuplicatesResponse`.
- [x] 1.3 `GET /jr-worklogs/duplicates` (роутер `jr_worklogs`/`sync_status`):
  період за `started_at` (дефолт `current_month`, валідація `start<=end`→400),
  scoped по `worker_key`, `401` без токена.

## 2. Backend — видалення дублів

- [x] 2.1 `app/services/jira/jira_service.py`: `delete_worklog(worklog_id,
  worker)` → `DELETE tempo-timesheets/4/worklogs/{id}` через `_make_request(...,
  raise_on_error=True)` (помилка не ковтається).
- [x] 2.2 `JRWorklogDAO`: хелпери для чистки — резолв «лишити один» (WST.target_id,
  інакше min `id`), `delete_by_ids`, перенацілення `WST.target_id` на залишений.
- [x] 2.3 Оркестрація чистки (`app/tasks/dedup_task.py` або метод): по кожній групі
  keep-one → `delete_worklog` кожного зайвого → видалити рядок `jr_worklogs` лише
  після успіху Tempo → перелінк WST; помилки збирати в `errors`, не валити все;
  повертати `{deleted, kept, groups, errors}`.
- [x] 2.4 `POST /jr-worklogs/dedup`: тіло з переліком груп/`worklog_id`; `400` без
  `worker_key`; обгорнути в `run_job` (`trigger_name="worklog.dedup-cleanup"`),
  щоб осідало в `api_jobs`; `401` без токена.

## 3. Backend — прапор дубля на календарі

- [x] 3.1 `TCEntriesDAO.get_calendar_blocks` (+`routers/calendar.py`/`schemas`):
  додати похідний `duplicate: bool` через переюз `find_duplicate_groups`
  (підзапит/мапа в пам'яті), не змінюючи набір станів синку.
- [x] 3.2 Перевірити інваріант: `service`/`tempo`/`synced` без змін; `duplicate`
  окремим полем; read-only, без alembic.

## 4. Frontend — закладка «Дублі» в профілі

- [x] 4.1 `api/types.ts`/`client.ts`: `WorklogDuplicateGroup`/`...Response`,
  `worklogDuplicates({start,end})`, `dedupWorklogs(groups)`.
- [x] 4.2 `ProfileView.vue`: третя закладка «Дублі» (`tab` тип + `tabs` масив +
  блок контенту); новий `components/profile/DuplicatesTab.vue` (PeriodPicker,
  перелік груп із членами, чекбокси, кнопка «Виправити обрані» зі спінером,
  підсумок, перезавантаження, помилка без worker_key).
- [x] 4.3 Кнопка «Оновити з Tempo» на закладці «Дублі»: викликає наявний
  `POST /sync/jira/worklogs` (переюз клієнт-методу пулу worklog-ів) за період зі
  спінером, далі перезавантажує групи; помилка без `worker_key` (`400`).
- [x] 4.4 i18n (UK+EN) для закладки/кнопок/підсумку; CSS у `data.css`.

## 5. Frontend — підсвітка дубля на календарі

- [x] 5.1 `api/types.ts` (`CalendarBlock.duplicate`), `lib/calendar.ts`
  (`PlacedBlock.duplicate`, проброс у `layoutWeek`).
- [x] 5.2 `components/calendar/CalendarBlock.vue`: окремий маркер при
  `duplicate=true` (поверх стану синку, не ховаючи блок) + CSS; показ у панелі
  деталей блоку.
- [x] 5.3 Фільтр (чип) «лише дублі» у фільтрах календаря (`CalendarFilters.vue` +
  `stores/calendar.ts`): показує лише блоки `duplicate=true`, комбінується з
  фільтрами проекту/статусу, впливає на тоталі.
- [x] 5.4 i18n підписи фільтра/підказки про дублі; `npm run build`
  (`vue-tsc`+`vite`) чисто.

## 6. Верифікація

- [x] 6.1 Backend наживо: `GET /jr-worklogs/duplicates` зареєстровано в OpenAPI
  живого контейнера, `401` без токена — PASS. `find_duplicate_groups` на синтетиці
  проти реальної БД (транзакція + ROLLBACK): групи `count>1`, scoped по
  `worker_key`, `None`-worker→[], поза-період→[], `is_linked` — 11/11 PASS.
  Валідація періоду — реюз доведеного `_period_or_400`. (HTTP-читання реальних
  дублів під токеном — у браузерному QA 6.5; форжинг токена заблоковано гардом.)
- [x] 6.2 Оркестрація чистки на синтетиці з **фейковим** Tempo-delete (транзакція +
  ROLLBACK, реального видалення немає): keep-one (canonical за `WST.target_id`,
  інакше min `id`), перелінк WST зайвого→canonical, видалення локального рядка лише
  по успіху, помилка Tempo одного→`errors` (решта прибрана) — 11/11 PASS.
  `delete_worklog`/`_make_request`: порожнє тіло (`204`)→успіх; `4xx`→`TempoApiError`
  з тілом — 5/5 PASS. (HTTP POST + `run_job`-аудит — у браузерному QA; реальні дублі
  чистити лише з підтвердження користувача.)
- [x] 6.3 `GET /calendar` віддає `duplicate=true` для блоку з відомим дублем —
  перевірено через `get_calendar_blocks`+логіку роутера на синтетиці (транзакція +
  ROLLBACK): e1(лінк на дубль)→`true`, e2(унікальний)→`false`, e3(без WST)→`false`,
  стани синку незмінні — 7/7 PASS; `CalendarBlock.duplicate` присутній у живій
  OpenAPI-схемі.
- [x] 6.4 `openspec validate add-worklog-dedup-cleanup --strict` — OK.
- [x] 6.5 Браузерний QA (на користувача): закладка «Дублі» показує групи, масовий
  фікс видаляє зайві зі спінером; календар маркує дубльовані блоки.
  **Підтверджено користувачем — працює.**
