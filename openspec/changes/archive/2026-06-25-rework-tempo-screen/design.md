## Context

Це фронтенд-фокусована зміна (з мінімальними backend-доповненнями), що завершує
уніфікацію дані-екранів. Усталений патерн уже застосовано до `/timecamp` і `/jira`
(`rework-timecamp-entries-screen`, `rework-jira-issues-screen`): `DataPage`,
`PeriodPicker`, спільні `SyncState`/`SyncFilter` (канонічний `SyncTri`, англ.
підписи), серверна пагінація, **явна** кнопка синку з попапом-описом. `/tempo`
лишився поза патерном.

Поточний `views/TempoView.vue` показує `worklog_sync_tasks` (`GET
/worklog-sync-tasks`) із чекбоксами, верхньою «Синхронізувати обрані» і трьома
кнопками-кроками (`prepare/resolve/push`) у тулбарі. Read-ендпоінта для `jr_worklogs`
(реальні Tempo-worklog-и) **немає** — є лише WST.

Залежність: per-user `sync_prefs` (модель/`/auth/me`/`PATCH /users/me/sync-prefs`)
постачає зміна `add-celery-auto-linking`; цей екран лише споживає їх у профілі.

## Goals / Non-Goals

**Goals:**

- `/tempo` під патерн `DataPage` із **двома вкладками** (реальні Tempo-worklog-и /
  конвеєр синку), періодом, фільтром, пагінацією.
- Попап-опис перед будь-якою дією синку; усі кнопки — у `#actions`.
- Пер-рядкова дія замість чекбоксів; кнопка «Забрати з Tempo».
- Екран «Профіль» із перемикачами автосинку (`sync_prefs`).
- Переюз спільних компонентів і «мови синку».

**Non-Goals:**

- Бекенд-автоматика, Celery, beat — у `add-celery-auto-linking`.
- Редагування/створення worklog-ів руками з UI (поза пушем) — поза скоупом.
- Адмінське редагування чужих `sync_prefs` — лише власні.

## Decisions

### D1. Дві вкладки — вкладені маршрути, як `ProjectsView`

`/tempo` стає контейнером із редіректом на дефолтну під-вʼюху; дочірні —
`/tempo/worklogs` (реальні Tempo-worklog-и) і `/tempo/pipeline` (WST-конвеєр).
Вкладки — `DataPage` `:tabs`/`v-model:active-tab` (router-agnostic; навігацію робить
вʼюха). Це дзеркалить наявний патерн «Проектів».
*Альтернатива:* in-view tab-стан без маршрутів — відкинуто (втрачається
deep-link/відновлення маршруту, що вже є патерном).

### D2. Read-ендпоінти обох вкладок — `GET /jr-worklogs` + розширення `/worklog-sync-tasks`

Вкладка «Tempo»: `GET /jr-worklogs?start&end&linked=all|linked|unlinked&q&limit&offset`
→ `{ items, total }`, scoped по `worker_key` із JWT (як `GET /tc-entries`/`/calendar`).
Похідне `is_linked` — через **EXISTS** на `worklog_sync_tasks` (`target_id =
jr_worklogs.id`). DAO-метод `list_with_link_state` за зразком
`TCEntriesDAO.list_with_sync_state`. Без міграції.

Вкладка «Конвеєр»: наявний `GET /worklog-sync-tasks` **розширюється** серверною
пагінацією (`limit`/`offset`/`total`), фільтром стану (`synced` = `target_id IS NOT
NULL`), пошуком `q` і полем `issue_name`; `summary` лишається.

**Назва задачі + пошук (D2a):** обидві вкладки показують `issue_key` **і назву**
задачі (резолв через join `jr_issues` за `issue_key`/`issue_id`); параметр `q` шукає
саме за **назвою** задачі (`ILIKE`), як пошук на `/jira`/`/timecamp`. У відповіді —
поле `issue_name` (може бути `null`, якщо задача локально невідома).

### D3. «Мова синку» — переюз `SyncState`/`SyncFilter` з контекстною семантикою

Обидві вкладки переюзовують канонічні `SyncState`/`SyncFilter` (`SyncTri`,
англ. підписи `Synced`/`Not synced`) — **без** власних стилів/підписів
(обовʼязковий патерн `systemPatterns`). Семантика «synced» різна:

- вкладка «Конвеєр»: `synced` = запушено в Tempo (`target_id IS NOT NULL` /
  `status = created`);
- вкладка «Tempo»: `synced` = звʼязаний із нашим WST (`is_linked`).

Вигляд і фільтр — однакові.

### D4. Пер-рядкова дія + per-id push-тригер

Замість чекбоксів і масової «Синхронізувати обрані» — пер-рядкова кнопка
(`SyncBtn`-патерн) на вкладці «Конвеєр», що синхронізує **один** `WorklogSyncTask`.
Бекенд: новий `POST /sync/worklog-tasks/{id}/push` (пуш одного task через наявну
`create_worklogs`-логіку, обмежену по id; той самий `api_jobs`-аудит).
*Чому окремий per-id, а не reconcile:* користувач хоче миттєву точкову дію на
конкретний рядок; reconcile — періодний/фоновий.

### D5. Кнопки й попапи — усе зверху, з описом

Усі дії — у слот `#actions` `DataPage`; ряд кнопок-кроків під шапкою прибрано.
Кожна агрегатна дія («Забрати з Tempo», «Синхронізувати все/конвеєр») відкриває
`Sheet`-попап (за `SyncEntriesModal`) з `PeriodPicker` і **пояснювальним текстом**,
що саме станеться, і лише тоді виконується. Кроки `prepare/resolve/push` більше не
експонуються окремими кнопками (їх поглинає автоматика/одна дія).

### D6. Екран «Профіль» — одна точка меню, дві закладки

У шаблоні меню user-chip мало два пункти («Профіль», «Налаштування»), які зараз
ведуть у пустоту. **Зводимо їх в один** пункт «Профіль» → новий `views/ProfileView.vue`
(маршрут `profile`) на `DataPage` з **двома закладками**:

- **«Особисті дані»** — **редагування** власних полів через `PATCH /users/me`:
  дозволено все, **крім** `email` і `is_active` (їх endpoint відхиляє/ігнорує) —
  `email` лишається адмінським (ключ match-by-email Google-входу), `is_active` —
  щоб користувач не вимкнув сам себе. Тобто редаговані принаймні `username` і
  `worker_key`; `email`/`is_active` показані read-only. **Пароль** — окремо, **через
  хешування** (`PATCH /users/me/password`, `bcrypt` `$2b$`, не «в лоб»): з перевіркою
  поточного, а для invite-користувача з `NULL`-хешем — **встановлення** першого пароля.
- **«Синхронізації»** — тумблер на кожен ключ `sync_prefs` (`auto_timecamp_pull`/
  `auto_jira_pull`/`auto_tempo_pull`/`auto_linking`/`auto_push_tempo`). Читання —
  `GET /auth/me.sync_prefs` (відсутність/`NULL` → **`false`**, автосинк opt-in);
  зміна — `PATCH /users/me/sync-prefs` (оптимістичне оновлення, відкат на помилку).

Підписи — двомовні (i18n): це налаштування, а не стан синку, тож «мова синку» тут не
застосовується.

## Risks / Trade-offs

- **Залежність від `add-celery-auto-linking`:** профіль-перемикачі без бекенд-`sync_prefs`
  не працюватимуть. → *Mitigation:* мерджити після backend-зміни; до того тумблери
  можна сховати за фіча-флагом / показувати disabled.
- **Два джерела «синку» на одному екрані** (jr_worklogs vs WST) можуть плутати. →
  *Mitigation:* чіткі назви вкладок + різні, але узгоджені підписи стану; пер-вкладкові
  hint-тексти в попапах.
- **Похідний `is_linked` через EXISTS** на великих обсягах. → *Mitigation:* той самий
  перевірений патерн, що `is_synced` у `/tc-entries`; період + пагінація обмежують
  вибірку.

## Resolved (рішення користувача 2026-06-24)

- **Пошук/назва на `/tempo`:** потрібні — показуємо назву задачі біля номера й
  додаємо пошук **за назвою** (`q`) на обох вкладках (D2/D2a).
- **Профіль:** меню user-chip зводимо до **одного** пункту «Профіль»; екран — **дві
  закладки** (особисті дані + синхронізації) (D6).
- **Дефолт `sync_prefs`:** `false`/`NULL` (opt-in) — узгоджено зі зміною
  `add-celery-auto-linking`.
- **Редаговані особисті дані:** self-edit (`PATCH /users/me`) дозволяє все, **крім**
  `email` і `is_active` (read-only/відхиляються); пароль — окремо через хешування
  (`PATCH /users/me/password`).

## Open Questions

- Немає відкритих питань.
