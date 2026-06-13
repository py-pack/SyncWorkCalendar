## Why

Дизайн Sync Work, окрім календаря, має чотири «дані»-екрани: таблиці
**TimeCamp** / **Jira** / **Tempo**, **Журнал синку** (api-jobs із кроком
підтвердження) і **Користувачі** (адмін заводить акаунти). Сьогодні все це
доступне лише через Swagger чи БД. Це **фаза 3 із трьох** — вона добудовує
решту екранів поверх уже наявного REST API і додає бракуючий бекенд там, де
екран без нього не працює (Users CRUD — за рішенням користувача; мінімальне
читання Jira-задач).

## What Changes

- **Frontend — таблиці даних:** спільний каркас (`PageHeader`, `Tabs`,
  `DataTable`, `StatusBadge`, кнопка синку зі станом) і три екрани:
    - **TimeCamp:** вкладки «Проекти» (тогл `is_sync`, маппінг `issue_key`,
      лічильник entries — через наявні `GET /tc-projects` + `PATCH
      /tc-projects/{id}`) і «Незіставлені» (`GET /tc-entries/untracked`);
      кнопки синку (`POST /sync/timecamp/projects|entries`).
    - **Jira:** вкладки «Проекти» (тогл `is_watched`, лічильник issues) і
      «Задачі»; кнопки синку (`POST /sync/jira/projects|issues`).
    - **Tempo:** конвеєр `worklog_sync_tasks` зі зведенням по статусах,
      масовий синк вибраних і кроки pipeline (`GET /worklog-sync-tasks` +
      наявні `POST /sync/worklog-tasks/prepare|resolve-issues|push-to-tempo`).
- **Frontend — Журнал синку:** таблиця `api_jobs` із фільтрами, рядок →
  бічна панель деталей (payload/result/error) і дія **підтвердити** на
  `needs_verification` (через наявні `GET /api-jobs`, `GET /api-jobs/{id}`,
  `POST /api-jobs/{id}/verify`).
- **Frontend — Користувачі:** таблиця користувачів (аватар, `worker_key`,
  активність, меню) і бічна форма «Запросити» (ім'я, e-mail, `worker_key`).
- **Backend — Users CRUD (`api-users-management`):** `GET /users`,
  `POST /users` (запросити: ім'я + e-mail + `worker_key`, **без пароля** —
  вхід через Google за e-mail; пароль опційний), `PATCH /users/{id}`
  (ім'я / `worker_key` / активність), `DELETE /users/{id}`.
- **Backend — зміна `api_users`:** `password_hash` → **nullable** (invite-флоу
  без пароля, вхід через Google). Відображуване ім'я — наявний `username`
  (окрему колонку `name` не додаємо, рішення користувача). Одна
  alembic-ревізія (лише `password_hash`).
- **Backend — мінімальне читання Jira (`api-jira-read`):** `GET /jr-issues`
  (список задач, фільтр за проектом/періодом) і `PATCH /jr-projects/{id}`
  (тогл `is_watched`) — потрібні, щоб Jira-екран працював (модель `JRIssue`
  вже є, endpoint-а немає).

Без breaking-змін: додаємо нові endpoint-и і поля, наявні контракти не
чіпаємо.

## Capabilities

### New Capabilities

- `frontend-data-tables`: спільний табличний каркас і три екрани (TimeCamp,
  Jira, Tempo) з тоглами, вкладками, синком і конвеєром worklog-задач.
- `frontend-sync-journal`: екран журналу `api_jobs` із фільтрами, деталями
  і кроком підтвердження `needs_verification`.
- `frontend-users`: екран управління користувачами — таблиця і форма
  «запросити» (без самостійної реєстрації).
- `api-users-management`: backend CRUD користувачів (`GET/POST/PATCH/DELETE
  /users`), invite-флоу без пароля (вхід через Google), nullable
  `password_hash` (відображуване ім'я — наявний `username`).
- `api-jira-read`: `GET /jr-issues` і `PATCH /jr-projects/{id}` (тогл
  `is_watched`) — мінімальний бекенд для Jira-екрана.

### Modified Capabilities

<!-- Наявні вимоги не змінюються: нові Jira-endpoint-и і Users CRUD —
     ADDED поверх існуючого API; контракти api-sync-status/api-jobs/
     api-tc-projects-management лишаються як є. -->

## Impact

- **Новий код (frontend):** `front/src/views/{TimeCampView,JiraView,
  TempoView,JournalView,UsersView}.vue`, `components/data/*` (табличний
  каркас, `StatusBadge`, `SyncBtn`), `stores/{tables,journal,users}.ts`,
  методи клієнта + типи.
- **Новий код (backend):** `app/api/routers/users.py`,
  `app/api/routers/jr_issues.py` (+ `PATCH` у `jr_projects.py`),
  `app/api/schemas/{users,jr_issues}.py`, `APIUserDAO`
  (`list`, `create`, `update`, `delete`), `JRIssuesDAO.list_filtered`.
- **БД:** `api_users.password_hash` → nullable (колонку `name` не додаємо —
  переюз `username`); одна alembic-ревізія; оновити `schema.md`.
- **Документація:** `api-reference.md` (Users CRUD, jr-issues), Memory Bank
  (`progress.md` — закрито «add-user-management-cli» частково; `decisinLog.md`
  — invite-без-пароля через Google).
- **Поза скоупом (відкладено, UI показує, дія вимкнена):**
    - **RBAC-ролі** (admin/member/viewer) — селектор ролі у формі є, але роль
      не персиститься/не енфорситься; окрема зміна `add-rbac`. Users CRUD поки
      доступний будь-якому авторизованому (single-user адмін-контекст).
    - **Untracked → issue matching** — кнопка «Зіставити» показана, але
      вимкнена; окрема зміна `add-untracked-matching`.
    - **`last_seen`** користувача — показ опційний («—», якщо немає).
- **Ризики:** «синхронізувати вибрані» у Tempo при наявному period-based
  pipeline може мапитись на період, а не на конкретні id — деталі в
  `design.md`.
