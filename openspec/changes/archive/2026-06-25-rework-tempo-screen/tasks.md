## 1. Backend — read-ендпоінти, пошук, per-id push, пароль

- [x] 1.1 DAO `JRWorklogDAO.list_with_link_state(worker_key, start, end, linked, q,
      limit, offset)` — `jr_worklogs` + похідний `is_linked` (EXISTS на
      `worklog_sync_tasks.target_id`) + `issue_name` (join `jr_issues`) + пошук `q`
      за назвою; фільтр/сорт + окремий COUNT (за зразком `list_with_sync_state`)
- [x] 1.2 Схеми `JRWorklogItem`/`JRWorklogsResponse` (з `is_linked`/`issue_name`);
      `GET /jr-worklogs` у `routers/sync_status.py` (період дефолт — поточний місяць,
      `linked`/`q` фільтри, `limit`≤200, scoped по `worker_key`)
- [x] 1.3 Розширити `GET /worklog-sync-tasks`: пагінація (`limit`/`offset`/`total`),
      фільтр стану `synced` (`target_id IS NOT NULL`), пошук `q` за назвою,
      `issue_name` у items; `summary` лишити по всьому періоду
- [x] 1.4 `POST /sync/worklog-tasks/{id}/push` у `routers/sync_triggers.py` (пуш
      одного WST через `create_worklogs`, `404` на відсутній id, `400` без
      `worker_key`, дедуп проти `jr_worklogs`)
- [x] 1.5 `PATCH /users/me` (self): редагування власних полів (`username`/`worker_key`
      тощо), `email`/`is_active` — відхилити (`422`)/ігнорувати; `401` без токена
- [x] 1.6 `PATCH /users/me/password` (self): звірка поточного пароля; для `NULL`-хешу
      — встановлення першого; `bcrypt` `$2b$`; `401` без токена

## 2. Frontend — API client і типи

- [x] 2.1 `api/types.ts`: `JRWorklog`/`JRWorklogsResponse` (з `issue_name`/`is_linked`),
      `issue_name` у WST-типі, `MeResponse.sync_prefs`, тип `SyncPrefs`
- [x] 2.2 `api/client.ts`: `jrWorklogs({start,end,linked,q,limit,offset})`,
      `worklogSyncTasks` з новими параметрами (`synced`/`q`/`limit`/`offset`),
      `syncJrWorklogs(period)`, `pushWorklogTask(id)`, `updateSyncPrefs(partial)`,
      `updateMe(partial)`, `changeMyPassword(payload)`

## 3. Frontend — store

- [x] 3.1 `stores/tables.ts`: стан вкладки «Tempo» (`jrWorklogs`, `tempoPeriod`,
      `tempoLinkFilter`, `tempoQuery`, `tempoOffset`/`tempoTotal`) + `loadJrWorklogs`/
      сетери (reset пагінації)
- [x] 3.2 `stores/tables.ts`: вкладка «Конвеєр» — період/`SyncFilter`/`q`/пагінація для
      WST, `loadWst`, `pushOneWst(id)`, `syncJrWorklogs(period)`; прибрати
      `syncWstPrepare/Resolve/Push` step-екшени з UI-шляху
- [x] 3.3 `stores/auth.ts`/новий `stores/profile.ts`: `sync_prefs` (`setSyncPref` з
      оптимістичним оновленням і відкатом), `updateMe`, `changeMyPassword`

## 4. Frontend — екран `/tempo`

- [x] 4.1 Маршрути: контейнер `/tempo` (редірект → `/tempo/worklogs`) + дочірні
      `/tempo/worklogs`, `/tempo/pipeline` (`router/index.ts`, `lib/nav.ts`)
- [x] 4.2 Переписати `views/TempoView.vue` на `DataPage` з `:tabs`/`v-model:active-tab`;
      підвʼюхи `views/tempo/TempoWorklogs.vue` і `views/tempo/TempoPipeline.vue`
- [x] 4.3 Тулбар обох вкладок: `PeriodPicker` + `SyncFilter` + **поле пошуку** +
      пагінація; усі агрегатні дії — у `#actions`
- [x] 4.4 Колонки обох вкладок показують `key` **і** назву задачі (`issue_name`);
      `SyncState`; дата `дд.мм.рррр` (`fmtDate`)
- [x] 4.5 Попап синку з пояснювальним текстом (`components/tempo/PullWorklogsModal.vue`,
      за зразком `SyncEntriesModal`): «Забрати з Tempo» (вкладка Tempo, у `#actions`).
      Окремого bulk-попапа конвеєра немає — пер-рядкова дія його заміняє (D4/D5;
      кроки `prepare/resolve/push` поглинає автоматика/per-id push)
- [x] 4.6 Вкладка «Конвеєр»: пер-рядкова кнопка дії (`SyncBtn`) → `pushOneWst(id)`;
      прибрати чекбокси й «Синхронізувати обрані»

## 5. Frontend — екран «Профіль» (`frontend-profile`)

- [x] 5.1 `components/UserChip.vue`: меню user-chip — **один** пункт «Профіль» (→
      `profile`); прибрати пункт «Налаштування» (меню живе в `UserChip`, не `AppShell`)
- [x] 5.2 `views/ProfileView.vue` (маршрут `profile`) на `DataPage` з двома закладками
      («Особисті дані» / «Синхронізації»)
- [x] 5.3 Закладка «Особисті дані»: форма редагування `username`/`worker_key`
      (`updateMe`), `email`/`is_active` — read-only; окрема форма зміни пароля
      (`changeMyPassword`)
- [x] 5.4 Закладка «Синхронізації»: `components/profile/SyncPrefsToggles.vue` —
      тумблери на кожен ключ `sync_prefs` (дефолт **вимкнено**), зміна →
      `updateSyncPrefs`
- [x] 5.5 i18n-ключі (UK+EN) для вкладок Tempo, попапів, пошуку, профілю й
      перемикачів; CSS

## 6. Перевірка

- [x] 6.1 `npm run build` (`vue-tsc --noEmit` + `vite`) — чисто
- [x] 6.2 Backend smoke: `GET /jr-worklogs` (200 + 401 + `linked`/`q`),
      `GET /worklog-sync-tasks` (пагінація/`synced`/`q`/`issue_name`),
      `POST /sync/worklog-tasks/{id}/push` (404/400; 200-пуш не ганяли, бо реальний
      запис у Tempo), `PATCH /users/me` (200; `email`/`is_active` → 422),
      `PATCH /users/me/password` (200/400-wrong/401 + invite-set) — 24/24 PASS наживо
- [ ] 6.3 Браузерний QA: дві вкладки, період/фільтр/пошук, назва задачі в рядку,
      попапи з описом, «Забрати з Tempo», пер-рядкова дія; профіль — обидві закладки
      (зміна пароля + перемикачі `sync_prefs`, дефолт вимкнено)
- [x] 6.4 `openspec validate rework-tempo-screen --strict` — OK
