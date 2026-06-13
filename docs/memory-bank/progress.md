# Progress

## Що працює

- Синхронізація проектів `TimeCamp` → таблиця `tc_projects` (включно з
  ієрархією, кольорами, архівним прапором).
- Синхронізація entries `TimeCamp` за період → `tc_entries` (з обчисленням
  `duration` через `Computed("EXTRACT(EPOCH FROM end_at - start_at)")`).
- Парсинг `description` entry на `meta.task` через `SyncTaskService` з кешем
  ключів проектів та regex-шаблонів.
- Синхронізація проектів `Jira` → `jr_projects`.
- Точкова синхронізація issue-ів `Jira` за ключами (`UpdateJiraTask.update_jira_issues`)
  + автозаповнення `jr_users` і `jr_projects` з фактів.
- Тягнення worklog-ів `Tempo` через `serch_worklogs_by_user` (typo у назві
  методу збережене для сумісності).
- Створення `WorklogSyncTask` (статус `pre_create`) для entries без пари
  у `worklog_sync_tasks`.
- Стадія `before_create` — підтягує відсутні `JRIssue` за ключами та
  переводить таски у `create`.
- `create_worklogs` — викликає `Tempo` POST `worklogs`, зберігає `target_id`
  і переводить таски в `created`.

## Що в роботі (OpenSpec)

- [`extract-projects-screen`](../../openspec/changes/archive/2026-06-13-extract-projects-screen/)
  — **заархівовано 2026-06-13 (17/20; секції 5.2–5.4 — браузерний QA — на живу
  перевірку). 3 capability-дельти злиті в `openspec/specs/` і канонічні:
  MODIFIED `web-app-shell`, `frontend-data-tables` (+ADDED «Екран «Проекти»»),
  `frontend-app`.** Фронтенд-онлі: винесено «Проекти»-таблиці (TimeCamp+Jira) з
  `/timecamp`/`/jira` у новий екран «Проекти» з вкладеними маршрутами
  `/projects/timecamp`·`/projects/jira` (`/projects` → редірект); `/timecamp` →
  лише незіставлені записи, `/jira` → лише задачі (обидва без `Tabs`). У навігації
  — **єдиний пункт «Проекти»** першим у секції «Дані» (під-вʼюхи TimeCamp/Jira —
  таби всередині екрана); пункти «Даних» → «TimeCamp · Записи»/«Jira · Задачі».
  Реалізація: `lib/nav.ts` (`NavItem.path/children`, `leafItems`),
  `router/index.ts` (вкладений `/projects` + redirect), `views/ProjectsView.vue`
  + `views/projects/{TcProjects,JrProjects}.vue`, спрощені `TimeCampView`/
  `JiraView`, `AppShell` (один лінк + active за `route.matched`),
  `stores/tables.ts` (авто-синк по
  екранах: `autoSyncProjects`/`autoSyncEntries`/`autoSyncIssues`), `i18n`.
  Бекенд не зачіпається. `npm run build` чисто; `validate --strict` — OK.
  Дельти capability: `frontend-data-tables`, `web-app-shell`, `frontend-app`.
  Деталі — `activeContext.md`. Лишилось: браузерний QA + git-commit.
- **Веб-UI за дизайном Sync Work — 3 зміни (2026-06-13; усі
  `validate --strict` валідні):**
  - [`add-web-ui-foundation`](../../openspec/changes/archive/2026-06-13-add-web-ui-foundation/)
    — **заархівована 2026-06-13** (44/44 задачі; браузерний QA підтверджено
    робочим end-to-end — логін/пароль + Google-вхід; код у робочому дереві,
    лишився git-commit). Дизайн-система +
    app shell + авторизація (Google popup/`code` + One Tap, серверна верифікація
    `google-auth`, match-by-email, колонка `api_users.email`, alembic head
    `c03728fbb1cf`, єдиний JWT). 5 capability злиті в `openspec/specs/` і
    канонічні: **нові** `web-design-system`, `web-app-shell`, `web-auth`,
    `api-google-auth` + **MODIFIED** `frontend-app`. Рішення — `decisinLog.md`
    → D-013 (Google-вхід), D-014 (front HTTP-клієнт: authed-by-default +
    токен через DI-provider).
  - [`add-calendar-timesheet`](../../openspec/changes/archive/2026-06-13-add-calendar-timesheet/)
    — **заархівовано 2026-06-13** (read-only візуалізація, D-016; реалізація +
    браузерний QA пройдено наживо). `GET /calendar` (read поверх
    `tc_entries`⋈`tc_projects`⋈WST, **без міграції**, alembic head
    `10b7dc50b00f`) + фронт-екран тижня (сітка, блоки 3 варіанти, стани
    `service`/`tempo`/`synced` + `failed` forward-compat, тулбар, фільтри,
    навігація тижнями, тоталі, панель деталей-перегляд). Backend:
    `routers/calendar.py`, `schemas/calendar.py`, `TCEntriesDAO.get_calendar_blocks`.
    Frontend: `CalendarView` + `components/calendar/*` + `stores/calendar.ts` +
    `lib/calendar.ts` + `styles/calendar.css` + `api.calendar`. `npm run build`
    чисто; 401-контракт перевірено. **2 нові capability злиті в `openspec/specs/`
    і канонічні: `api-calendar`, `frontend-calendar`.** Редагування/sync/round-trip
    і колонка `billable` — у майбутні `add-calendar-editing` /
    `add-worklog-update-flow`.
  - [`add-data-screens`](../../openspec/changes/archive/2026-06-13-add-data-screens/) —
    **заархівовано 2026-06-13** (29/35; секція 9 QA — частково живцем, решта
    відкладена). Backend: Users CRUD (invite без пароля → Google; `password_hash
    → nullable`, alembic head `10b7dc50b00f`), Jira-read (`GET /jr-issues`, `PATCH
    /jr-projects/{id}`); smoke 16/16 PASS. Frontend: каркас таблиць + 5 екранів +
    stores; `npm run build` чисто; період читання 6 міс + авто-синк при відкритті.
    Ім'я користувача = наявний `username` (без колонки `name`, D-015). **5 нових
    capability злиті в `openspec/specs/`** (`frontend-data-tables`,
    `frontend-sync-journal`, `frontend-users`, `api-users-management`,
    `api-jira-read`) і канонічні.
  - Відкладено окремими майбутніми змінами: RBAC-ролі, untracked→issue
    matching, редагування календаря (`add-calendar-editing`), update/delete
    worklog-ів у Tempo (`add-worklog-update-flow`).
- [`restructure-monorepo-frontend`](../../openspec/changes/archive/2026-06-12-restructure-monorepo-frontend/)
  — заархівована **2026-06-12** (end-to-end запуск підтверджено). Монорепо:
  бекенд `api/` (пакет `app`, переїхав із `src/`), фронт `front/` (Vue 3 +
  Vite + TS, vue-router, Pinia, `fetch`), мультисервісний Docker на корені з
  dev hot-reload, host-nginx на доменах `sync.loc`/`sync.dev`, дворівневі
  інструкції агентів, host-порти за конвенцією (продукт 33: api `10331`,
  front `10332`, db `11331`). Доменна логіка/схема БД не зачіпались (alembic
  head `ef2c7288bbb0`). 4 capability злиті в `openspec/specs/`
  (`monorepo-layout`, `frontend-app`, `container-orchestration`,
  `workspace-conventions`). Деталі — `decisinLog.md` → D-012.
- [`add-rest-api`](../../openspec/changes/archive/2026-06-12-add-rest-api/)
  — заархівована **2026-06-12**: REST API підтверджено робочим, 5
  capability-специфікацій злиті в `openspec/specs/`. Тех-довідка —
  `docs/technical/api-reference.md`.

## Що працює (HTTP API)

- FastAPI app (`app/api/app.py`) із CORS і глобальними exception handler-ами.
  Старт — `run_api.py` / `make serve` (підтверджено робочим 2026-06-12).
- JWT auth (`/auth/login`, `/auth/refresh`, `/auth/me`) поверх `api_users`;
  паролі хешуються прямим `bcrypt` (`app/api/auth.py`, формат `$2b$`).
- `api_jobs` lifecycle (`running → needs_verification → verified`, або
  `running → failed`) — wrapper `app/api/jobs_wrapper.run_job`.
- Read-endpoints: `/tc-projects` (з `entries_count`), `/jr-projects` (з
  `issues_count`), `/worklog-sync-tasks` (із summary), `/tc-entries/untracked`.
- PATCH `/tc-projects/{id}` з `extra=forbid` і регексом для `issue_key`.
- 8 sync-trigger endpoint-ів з опційним `?background=true`.

## Що не реалізовано

- Сценарій оновлення (`pre_update → update → updated`) і видалення раніше
  створених worklog-ів у `Tempo` — статуси оголошені, логіки немає; винесено в
  майбутню `add-worklog-update-flow` (активується редагуванням/видаленням
  `synced`-блоку календаря).
- Редагування календаря (CRUD блоків, drag/resize/split/duplicate/delete,
  per-block і масовий sync, колонка `billable`) — майбутня `add-calendar-editing`
  (календар поки read-only, D-016).
- Тести (юніт/інтеграційні) і CI.
- Повноцінне управління користувачами — **частково закрито** зміною
  `add-data-screens`: є CRUD через API (`GET/POST/PATCH/DELETE /users`, invite
  без пароля → Google) + CLI `add_user`. Лишилось окремою зміною
  `add-user-management-cli`: set-password через API, CLI list/deactivate.
- TTL/cron для старих `api_jobs` — `add-api-jobs-cleanup`.
- RBAC, per-user OAuth-токени на Jira/TimeCamp — окремі майбутні зміни.

## Поточний стан гілки

- Branch: `main`.
- Незакомічене: `M main.ipynb` (зміна періоду на 2026-04-08…2026-04-13)
  плюс імпементація `add-rest-api` (нові файли `app/api/`, `app/models/api_*.py`,
  `app/dao/api_*_dao.py`, `run_api.py`, alembic-ревізія `ef2c7288bbb0`),
  а також сесія 2026-06-12: `app/cli/`, `Makefile`, `.python-version` (3.14),
  перехід `passlib → bcrypt` у `pyproject.toml`/`app/api/auth.py`,
  міграція `poetry → uv` (`uv.lock`).
- Остання міграція: `10b7dc50b00f` (2026-06-13, `make_password_hash_nullable_api_users`;
  попередня — `c03728fbb1cf` `add_email_to_api_users`). Застосовано.
- Алембік head відповідає поточним моделям після застосування ревізії.

## Відомі тех-борги

- Typo `worllog_sync_task.py` / `WorllogSyncTask` — не виправлено через
  ризик зачепити імпорти.
- `DatabaseHelper` у `core/db_helper.py` помічений як `deprecated`, але не
  видалений.
- `BaseDAO._sync` видаляє моделі, відсутні у вхідному DTO — для повних дампів
  безпечно, для часткових — небезпечно (використовуйте `update_by_keys` або
  `sync_all_between`).
- `JiraService.search_issues` — у блоках `creator`/`reporter` перевіряється
  `if project_field is not None` замість відповідних `*_field` (баг).

Деталі рішень — у `decisinLog.md`.
