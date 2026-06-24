## 1. Backend — JiraService (пагінація + JQL за проектами + фікс бага)

- [x] 1.1 Винести парсинг `issue (dict) → JiraIssueDTO` зі `search_issues` у спільний
  приватний хелпер (`JiraService._parse_issue`); **полагоджено баг**: `creator`
  будується при `creator_field is not None`, `reporter` — при `reporter_field is not
  None`. Додано null-safety (`parent`/`issuetype`/`priority`/`status`/
  `aggregateprogress` через `or {}`). `search_issues(keys)` переведено на хелпер.
- [x] 1.2 Додано приватний `JiraService._search(jql, *, page_size=None)` —
  POST `api/2/search` у циклі `startAt`/`maxResults`, акумулюючи `issues`, доки
  зібрано всі (спин і за `startAt >= total`, і за порожньою/неповною сторінкою).
  (Замість публічного `search_issues_by_jql` — приватний `_search`, переюзований
  обома публічними методами.)
- [x] 1.3 Публічний `JiraService.search_issues_by_projects(project_keys, *,
  page_size=100)` будує JQL `project in ("KEY",…)` (квотовані ключі) і кличе
  `_search`.

## 2. Backend — задача повного витягу

- [x] 2.1 Додано `UpdateJiraTask.update_issues_for_watched_projects()`: читає ключі
  watched-проектів, при порожньому — `return 0`; інакше `search_issues_by_projects`
  + upsert через `JRIssuesDAO.sync_by_key` (НЕ `sync_all`). Повертає кількість.
- [x] 2.2 Додано `JRProjectDAO.watched_keys(db)` (`select key where is_watched`).

## 3. Backend — ендпоінт

- [x] 3.1 Додано `_do_jr_issues_all()` у `routers/sync_triggers.py` (`synced`/
  `total`/`delta` через `_count` `JRIssue`, як інші `_do_*`).
- [x] 3.2 Додано `POST /sync/jira/issues-all` (auth, `?background=true`) через
  `_execute(trigger_name="sync.jira.issues-all", …)`. Тіло не потрібне.

## 4. Backend — перевірка контракту

- [x] 4.1 Прогнати сервер; перевірити OpenAPI (`/docs`) на новий
  `POST /sync/jira/issues-all`; `401` без токена. → на живому контейнері
  (`:10331`, hot-reload) ендпоінт присутній (method `post`); `401` без токена ✓.
- [x] 4.2 Smoke наживо: витяг watched-проектів за період активності збільшує
  `jr_issues` і тягне задачі без worklog-ів та не-заасайнені; пагінація вибирає всі
  сторінки. → **401-гейт ✓ автоматично**; авторизований витяг підтверджено
  **користувачем наживо** 2026-06-23 («все працює»).

## 5. Frontend — клієнт і стор

- [x] 5.1 `front/src/api/client.ts`: `syncJrIssuesAll(period)` →
  `POST /sync/jira/issues-all` із тілом періоду.
- [x] 5.2 `front/src/stores/tables.ts`: дія `syncJrIssuesAll(period)` (виклик API →
  `loadJrIssues()` reload; помилку кидає, щоб попап показав). (Пост-QA пивот: період
  обовʼязковий; `store.syncJrIssues` worklog-потік видалено.)

## 6. Frontend — дія в UI

- [x] 6.1 На екран `/jira` — **єдина** кнопка синку в `#actions`
  (`views/JiraView.vue`, іконка `cloudDown`), що відкриває попап `SyncIssuesModal`
  (`PeriodPicker`) → витяг за період; помилка — банером `DataPage`. (Пост-QA пивот:
  окрему пряму кнопку й period-worklog-синк прибрано — одна дія.)
- [x] 6.2 i18n (UK+EN): `jr_sync` / `jrsync_title` / `jrsync_hint` під витяг задач за
  період (ключ `jr_pull_all` видалено після зведення в одну кнопку).

## 7. Перевірка

- [x] 7.1 `npm run build` (`vue-tsc --noEmit` + `vite build`) — чисто.
- [x] 7.2 Браузерний QA наживо: витяг за період наповнює `/jira` задачами без
  worklog-ів і «загальними»; список перезавантажується; відсутність авто-синку. →
  **підтверджено користувачем наживо** 2026-06-23 («все працює»).
- [x] 7.3 `openspec validate add-jira-full-issue-pull --strict` — OK.

## Пост-QA пивот (фідбек користувача наживо)

- **Витяг — за період активності (`updated`), не «все»/`created`:**
  `search_issues_by_projects(keys, updated_from, updated_to)` будує JQL `project in
  (…) AND updated >= "from" AND updated <= "to 23:59" ORDER BY updated DESC`;
  `update_issues_for_watched_projects(updated_from, updated_to)`;
  `POST /sync/jira/issues-all` приймає опційний `PeriodBody` (без тіла — усі задачі).
- **Єдина кнопка на `/jira`:** замість окремої «повний витяг»-кнопки + period-синку
  worklog-ів — **одна** кнопка, що відкриває попап `SyncIssuesModal` (з
  `PeriodPicker`) → `store.syncJrIssuesAll(period)` → `POST /sync/jira/issues-all`
  з періодом → reload. `cloudDown`-кнопку прямого витягу й `store.syncJrIssues`
  (worklog-потік) прибрано; `jr_pull_all` i18n видалено; `jr_sync`/`jrsync_*`
  переписані під витяг задач.
- Live OpenAPI: `issues-all` приймає `PeriodBody`; 401-гейт ✓. Спека/`design.md`
  оновлені; `npm run build` чисто; `validate --strict` OK. Лишилось 4.2/7.2 (жива
  перевірка з токеном/у браузері).
