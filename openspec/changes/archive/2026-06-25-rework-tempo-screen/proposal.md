## Why

Екран `/tempo` лишився єдиним дані-екраном **поза** усталеним патерном
(`/timecamp`, `/jira`): він показує `worklog_sync_tasks` із чекбоксами й рядом
ручних кнопок-кроків (`prepare/resolve/push`) під шапкою, без вибору періоду,
фільтрів і попапів. Користувач натискає кнопку, не розуміючи, що вона робить, а
кнопки «забрати Tempo з сервера» там узагалі немає. Цю зміну робимо слідом за
бекенд-автоматизацією (`add-celery-auto-linking`), щоб екран показував те, що в БД,
а синк ішов **явними** діями з описом.

## What Changes

- **Дві вкладки** на `/tempo` (router-agnostic, як `ProjectsView`):
  - **«Tempo»** — реальні Tempo-worklog-и з БД (`jr_worklogs`), «що реально
    залоговано»; стан = чи звʼязаний worklog із TimeCamp-записом.
  - **«Конвеєр синку»** — `worklog_sync_tasks` (міст TimeCamp→Tempo); стан =
    запушено в Tempo (`target_id`).
- **Усі дії — зверху** (слот `#actions` `DataPage`); прибрати ряд кнопок під шапкою.
- **Попап з описом дії перед виконанням** (за зразком `SyncEntriesModal`/
  `SyncIssuesModal`: `Sheet` + `PeriodPicker` + пояснювальний текст) — щоб дія не
  спрацьовувала «наосліп».
- **`PeriodPicker`** (календар), **`SyncFilter`** (`All | Synced | Not synced`) і
  **пошук за назвою задачі** — як на `/timecamp`/`/jira`. Серверна пагінація.
- **Назва задачі біля номера:** кожен рядок показує `key` **і назву** задачі
  (резолв через `jr_issues`); пошук у фільтрах — саме за цією назвою.
- **Прибрати чекбокси й «Синхронізувати обрані»** → **пер-рядкова кнопка дії**
  (одиночна синхронізація рядка) на вкладці «Конвеєр синку».
- **Кнопка «Забрати з Tempo»** (`POST /sync/jira/worklogs`) — тягне `jr_worklogs` із
  сервера; екран показує те, що в БД.
- **Новий read-ендпоінт `GET /jr-worklogs`** (період, фільтр звʼязку, пошук `q`,
  пагінація, `issue_name`) — для вкладки «Tempo» (за прецедентом `GET /tc-entries`);
  наявний `GET /worklog-sync-tasks` розширюється пагінацією, фільтром стану, `q` та
  `issue_name`.
- **Один пункт «Профіль» у меню user-chip** (замість двох пустих «Профіль»/
  «Налаштування») → екран профілю з **двома закладками**: *Особисті дані*
  (редагування власних полів **крім** `email`/`is_active`, які read-only + зміна
  пароля через хешування) і *Синхронізації* (тумблери `sync_prefs`). Читання —
  `GET /auth/me`; self-edit полів — `PATCH /users/me`; пароль — `PATCH
  /users/me/password`; перемикачі — `PATCH /users/me/sync-prefs`. Автосинк **opt-in**:
  `sync_prefs` за дефолтом `false` (вимкнено), тумблери вмикають свідомо.
- Зберегти **єдину мову синку** (`SyncState`/`SyncFilter`, англ. підписи) — патерн
  `systemPatterns`.

## Capabilities

### New Capabilities
- `frontend-profile`: екран «Профіль» поточного користувача з **двома закладками** —
  особисті дані (ідентичність + зміна пароля) і перемикачі per-user автосинку
  (`sync_prefs`).

### Modified Capabilities
- `frontend-data-tables`: «Екран Tempo» переписано — дві вкладки, період, фільтри,
  **назва задачі + пошук за нею**, попапи з описом, пер-рядкова дія, кнопка «Забрати з
  Tempo» (замість чекбоксів і ряду кнопок-кроків).
- `api-sync-status`: новий `GET /jr-worklogs` (read `jr_worklogs` за період + фільтр
  звʼязку + пошук `q` + `issue_name` + пагінація); `GET /worklog-sync-tasks`
  розширено пагінацією, фільтром стану, `q` та `issue_name`.
- `api-sync-triggers`: per-id тригер пушу одного `WorklogSyncTask` (для пер-рядкової
  дії «синхронізувати рядок»).
- `api-users-management`: self-service `PATCH /users/me` (редагування власних полів,
  крім `email`/`is_active`) і `PATCH /users/me/password` (зміна пароля через хешування).
- `api-auth`: `GET /auth/me` додатково віддає `email` і `is_active` (read-only для
  екрана «Профіль»; self-edit їх не змінює).
- `web-app-shell`: маршрут `profile` і **єдиний** пункт «Профіль» у меню user-chip
  (замість двох) ведуть на новий екран.

## Impact

- **Frontend:** `views/TempoView.vue` (переписати на `DataPage` з вкладками),
  нові `components/tempo/*` (попап(и) синку, пер-рядкова дія), новий
  `views/ProfileView.vue` (дві закладки) + `components/profile/*`, `stores/tables.ts`
  (стан Tempo: період/фільтр/пошук/офсет/вкладка, `jrWorklogs`/`wst`), `stores/auth.ts`
  або новий `stores/profile.ts` (`sync_prefs`, зміна пароля), `api/client.ts`+`types.ts`
  (`jrWorklogs`, `syncJrWorklogs`, `pushWorklogTask`, `updateSyncPrefs`,
  `changeMyPassword`), `components/AppShell.vue` (один пункт user-chip),
  `router`/`lib/nav.ts` (маршрут профілю), `i18n/strings.ts` (нові ключі), CSS.
- **Backend:** новий `GET /jr-worklogs` (роутер `sync_status.py` + DAO-метод
  читання `jr_worklogs` з похідним `is_linked` + `issue_name` через join `jr_issues`
  + `q`); розширення `GET /worklog-sync-tasks` (пагінація, фільтр стану, `q`,
  `issue_name`); per-id `POST /sync/worklog-tasks/{id}/push`; self-service
  `PATCH /users/me` (крім `email`/`is_active`) і `PATCH /users/me/password`. Без міграції.
- **Залежність:** споживає per-user `sync_prefs` API з `add-celery-auto-linking`
  (бажано мерджити після нього).
