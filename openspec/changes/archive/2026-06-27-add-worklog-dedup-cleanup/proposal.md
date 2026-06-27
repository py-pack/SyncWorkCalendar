## Why

Через подвійний запуск ретраю (першопричину усуває зміна `harden-job-retry`) у Tempo
вже накопичились **дублі worklog-ів**: один TimeCamp-запис відображено двома (й
більше) Tempo-worklog-ами з тим самим `(issue, worker, started_at, duration)`. Їх
видно лише сирим SQL по `jr_worklogs`, а прибрати немає чим — `JiraService` уміє
лише `create`/`update`, видалення в Tempo не реалізовано. Потрібен (1) спосіб
**знайти** такі дублі, (2) **масово прибрати** зайві (залишивши один), (3)
**підсвітити** їх на календарі, щоб бачити проблему до чистки.

## What Changes

- **Новий backend-механізм пошуку дублів:** `GET /jr-worklogs/duplicates` —
  групує `jr_worklogs` поточного `worker_key` за **тим самим ключем дедупу**, що й
  `JRWorklogDAO.find_match` (`jr_issues_id` + `jr_worker_key` + `started_at` +
  `duration`), `HAVING count(*) > 1`, за період (дефолт — поточний місяць). Повертає
  групи з ключем, задачею (`key`/`name`), кількістю і переліком worklog-ів групи.
- **Новий backend-механізм чистки:** `POST /jr-worklogs/dedup` — для кожної обраної
  групи **лишає один** worklog (канонічний: на який вказує наявний `WST.target_id`,
  інакше — з найменшим `id`) і **реально видаляє решту з Tempo** через **новий**
  `JiraService.delete_worklog` (`DELETE tempo-timesheets/4/worklogs/{id}`), чистить
  локальне дзеркало `jr_worklogs` і **перенацілює** будь-який `WST.target_id`, що
  вказував на видалений worklog, на залишений. Дія аудиториться в `api_jobs`. Без
  `worker_key` — `400`.
- **Frontend — третя закладка «Дублі» на екрані «Профіль»:** перелік груп дублів за
  період (`PeriodPicker`), вибір груп чекбоксами і кнопка **«Виправити обрані»** →
  синхронний виклик чистки зі спінером → підсумок (скільки видалено) → перезавантаження.
- **Календар — підсвітка дублів:** `GET /calendar` додає кожному блоку прапор
  `duplicate`, а екран календаря **візуально маркує** блок, чий worklog входить у
  групу дублів (видно і в панелі деталей).

## Capabilities

### New Capabilities

- `api-worklog-dedup`: виявлення і чистка дубльованих Tempo-worklog-ів —
  `GET /jr-worklogs/duplicates` (групи дублів за період) і `POST /jr-worklogs/dedup`
  (масове видалення зайвих із Tempo + чистка локального дзеркала й перелінк WST),
  плюс новий `JiraService.delete_worklog`.

### Modified Capabilities

- `frontend-profile`: вимога «Екран «Профіль»» розширюється з **двох** закладок до
  **трьох** (додається «Дублі»); додається вимога поведінки закладки «Дублі»
  (перелік груп + масовий фікс).
- `api-calendar`: блок календаря отримує додатковий булевий прапор `duplicate`
  (true, якщо у періоді ≥2 `jr_worklogs` з тим самим ключем дедупу, що в блоку);
  статуси `service`/`tempo`/`synced` не змінюються — це **окремий** прапор.
- `frontend-calendar`: блок із `duplicate = true` MUST візуально маркуватися
  (окремо від стану синку) і показувати позначку в панелі деталей.

## Impact

- **Backend:** новий `app/services/jira/jira_service.py → delete_worklog` (Tempo
  `DELETE`); `app/dao/jr_worklog_dao.py` (`find_duplicate_groups`, `delete_by_ids`);
  можливо новий `app/tasks/dedup_task.py` (оркестрація keep-one + delete + relink);
  роутер `app/api/routers/sync_status.py` або `jr_worklogs`-роутер
  (`GET /jr-worklogs/duplicates`, `POST /jr-worklogs/dedup`, обгорнутий у
  `run_job`); `routers/calendar.py` + `TCEntriesDAO.get_calendar_blocks` (прапор
  `duplicate`); схеми. **Без alembic** — нових колонок немає, дублі рахуються
  `GROUP BY`, чистка видаляє рядки (head `69dde0d17ff2`).
- **Frontend:** `front/src/views/ProfileView.vue` (третя закладка) + новий
  `components/profile/DuplicatesTab.vue`; `api/types.ts`/`client.ts`
  (`worklogDuplicates`, `dedupWorklogs`); `stores/` (стан дублів);
  `components/calendar/CalendarBlock.vue` + `lib/calendar.ts` + `api/types.ts`
  (`duplicate`-прапор і його рендер); i18n; CSS.
- **Незворотність:** масовий фікс **видаляє worklog-и з Tempo** — операція
  незворотна (свідоме рішення користувача).
