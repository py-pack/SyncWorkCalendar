# Active Context

## Дата оновлення

2026-06-13 — **фази 1 і 3 заархівовані**; код обох у робочому дереві, не
закомічено. Фаза 2 (`add-calendar-timesheet`) — на proposal-стадії.

## Статус фази 3 (`add-data-screens`) — заархівовано 2026-06-13

Реалізовано (29/35 задач; секція 9 «ручний QA» — частково пройдено живцем, решта
відкладена). Зміна заархівована в
[`archive/2026-06-13-add-data-screens/`](../../openspec/changes/archive/2026-06-13-add-data-screens/);
**5 нових capability злиті в `openspec/specs/` і канонічні**:
`api-users-management`, `api-jira-read`, `frontend-data-tables`,
`frontend-sync-journal`, `frontend-users`. Три відкриті питання design.md
закриті рішеннями користувача (D-015): `name` → переюз `username`; `last_seen` і
точковий `ids[]` для Tempo — відкладено. Браузерний QA-рефінмент: період читання
розділено зі sync-періодом + авто-синк при відкритті (теж D-015).

- **Backend:** `api_users.password_hash → nullable` (alembic head
  **`10b7dc50b00f`**, застосовано); Users CRUD (`GET/POST/PATCH/DELETE /users`,
  invite без пароля → Google-вхід, дублі email/username → `409`, NULL-хеш login →
  `401`); Jira-read (`GET /jr-issues?project_id`, `PATCH /jr-projects/{id}` тогл
  `is_watched`). Smoke-тест 16/16 проти живої БД — PASS. Побічний фікс:
  `config.py` `extra="ignore"` (спільний `.env` з `VITE_*` ламав локальний
  старт). Рішення — `decisinLog.md` → **D-015**.
- **Frontend:** табличний каркас (`DataTable` generic, `Tabs`, `PageHeader`,
  `StatusBadge`, `SyncBtn`, `ProjTag`), 5 екранів (TimeCamp/Jira/Tempo/Журнал/
  Користувачі), stores `tables`/`journal`/`users`, методи клієнта + типи,
  динамічний бейдг `needs_verification` у навігації, нові стилі `data.css`
  (порт `tables.css`). `npm run build` (`vue-tsc` + `vite`) — чисто.
- **Залишок:** браузерний QA (секція 9) і git-commit.

## Статус фази 1 (`add-web-ui-foundation`) — заархівована 2026-06-13

Реалізовано (44/44 задачі; браузерний QA — секція 9 — **підтверджено робочим
2026-06-13**: логін/пароль і Google-вхід працюють end-to-end). Зміна
заархівована в
[`archive/2026-06-13-add-web-ui-foundation/`](../../openspec/changes/archive/2026-06-13-add-web-ui-foundation/);
5 capability злиті в `openspec/specs/` і є канонічними: **нові**
`web-design-system`, `web-app-shell`, `web-auth`, `api-google-auth` +
**MODIFIED** `frontend-app` (auth-gated роутинг на 6 екранів).

**Операційні нюанси (Docker), доведені при ввімкненні Google-входу 2026-06-13:**
(1) `VITE_GOOGLE_CLIENT_ID` (публічний) прокинуто у front-сервіс через
`docker-compose.yml` — Vite не читає кореневий `.env`; (2) `google-auth`
довстановлено у venv api (`uv sync` у контейнері), бо анонімний `/app/.venv`-том
застарів після додавання залежності й валив старт із `ModuleNotFoundError`.
Симптоми, команди й env-розподіл — `docs/technical/dev-environment.md` (§4, §7).

- **Backend:** колонка `api_users.email` (`UNIQUE`, nullable; alembic head
  `c03728fbb1cf`, **застосовано**); `APIConfig.google_client_id/secret`;
  `APIUserDAO.get_by_email` (lower-case, лише активні); `POST /auth/google`
  (`google-auth`-верифікація credential / обмін code; match-by-email; єдиний
  JWT; `401 "account not found"`; `503` без конфігу). Рішення — `decisinLog.md`
  → **D-013**. Verified live: `503`/`422`/`401` + `code`-без-secret `503`.
- **Frontend:** дизайн-система (токени/теми/акценти/щільність, 12 UI-примітивів,
  іконки, Geist-шрифти), i18n UK/EN (`useI18n` поверх `ui.lang`), dot-path
  storage-обгортка (D7), stores `ui`/`auth`, `api/client` (authed-by-default +
  токен через DI-provider + 401-хук, **D-014**), app shell (нав-секції, collapse,
  user-chip, Tweaks), `vue-router` на 6 екранів (StubView — фази 2–3), auth-gate,
  екран входу (логін/пароль + Google popup/`code` + One Tap). `npm run build`
  (`vue-tsc` + `vite`) — чисто.
- **Залишок:** лише git-commit (реалізація + архів лежать у робочому дереві
  незакоміченими — коміт за рішенням користувача).

## Поточний фокус

**Перенесення дизайну Sync Work у фронт — 3 OpenSpec-зміни (фази 1 і 3 —
заархівовані 2026-06-13; фаза 2 — proposal).** Джерело — handoff-бандл із Claude Design, який лежить **локально в
[`docs/design/`](../design/)** (прототип React+CSS у `docs/design/project/src/*`,
наявний OpenAPI — `docs/design/project/uploads/sync.work.json`). 7 екранів:
авторизація, календар, таблиці TimeCamp/Jira/Tempo, журнал синку,
користувачі; двомовність UK/EN, світла/темна теми, Tweaks. Розбито на 3
послідовні фази:

1. [`add-web-ui-foundation`](../../openspec/changes/archive/2026-06-13-add-web-ui-foundation/)
   — **заархівована 2026-06-13.** Дизайн-система
   (токени/теми/примітиви/іконки/i18n/Tweaks), app shell
   (навігація, маршрути, auth-gate, user-chip), екран входу і **Google-вхід**
   (popup + One Tap, серверна верифікація, match-by-email до `api_users`,
   без авто-реєстрації; нова колонка `api_users.email`).
2. [`add-calendar-timesheet`](../../openspec/changes/add-calendar-timesheet/) —
   тижневий timesheet (головний екран) із **повним редагуванням блоків і
   записом на бекенд**: drag/resize/split/duplicate/delete + sync; новий
   `GET /calendar` і CRUD `/calendar/blocks`; редаговний блок =
   `worklog_sync_tasks` (+ `billable`), TimeCamp read-only; редагування
   synced-блоку активує зарезервовані `pre_update→update→updated` і
   update/delete worklog у Tempo.
3. [`add-data-screens`](../../openspec/changes/archive/2026-06-13-add-data-screens/) —
   **заархівовано 2026-06-13** (див. статус вище). Таблиці TimeCamp/Jira/Tempo,
   журнал `api_jobs` (з verify), користувачі + **Users CRUD** (`/users`, invite
   без пароля → вхід через Google; **ім'я = наявний `username`**, nullable
   `password_hash`) і мінімальний Jira-read (`GET /jr-issues`,
   `PATCH /jr-projects/{id}`).

**Свідомо відкладено** (UI показує, дія вимкнена; окремі майбутні зміни):
RBAC-ролі (admin/member/viewer), untracked→issue matching. Усі 3 зміни
валідні (`openspec validate --strict`). Деталі рішень — у `design.md`
кожної зміни.

Попередня зміна
[`restructure-monorepo-frontend`](../../openspec/changes/archive/2026-06-12-restructure-monorepo-frontend/)
заархівована 2026-06-12 — **end-to-end запуск підтверджено** користувачем
(стек піднявся, домени `sync.loc`/`sync.dev` і HMR працюють). 4 нові
capability-специфікації злиті в `openspec/specs/` (`monorepo-layout`,
`frontend-app`, `container-orchestration`, `workspace-conventions`) і є
канонічними.

Підсумок результату (канонічні деталі — у `systemPatterns.md`/`techContext.md`/
`decisinLog.md` → D-012):

- **Монорепо:** бекенд у `api/` (пакет `app`, переїхав із `src/`, ~90
  імпортів), фронт у `front/` (Vue 3 + Vite + TS, `vue-router`, Pinia,
  `fetch`-клієнт). Docker / кореневий `Makefile` / `docs/` / `openspec/` —
  спільні на корені. Дворівневі інструкції агентів (кореневі роутери +
  per-folder `AGENTS.md`/`CLAUDE.md` з легкими вказівниками).
- **Env:** `app/config.py` вантажить env абсолютними шляхами, пріоритет
  `api/.env.template` → `<root>/.env` → `api/.env`.
- **Host-порти (конвенція, продукт 33):** api `10331`, front `10332`,
  db `11331` (схема `TT AA S`; скіл `preferred-docker-images`).
- **Dev:** `docker compose up` (hot-reload обох сервісів) або host-run
  (`make dev`/`make front-dev` + db у docker); доступ через host-nginx
  (`docker/nginx.loc.conf`) на двох доменах. Гайд —
  [`docs/technical/dev-environment.md`](../technical/dev-environment.md).

Доменна логіка, моделі та схема БД не змінювалися (alembic head
`ef2c7288bbb0`). **Незакомічене:** уся реалізація лежить у робочому дереві —
коміт за рішенням користувача.

Попередня зміна
[`add-rest-api`](../../openspec/changes/archive/2026-06-12-add-rest-api/)
заархівована 2026-06-12: REST API на FastAPI підтверджено робочим
(сервер стартує через `run_api.py`/`make serve`, ручний smoke-test
пройдено). Її 5 capability-специфікацій злиті в `openspec/specs/`
(`api-auth`, `api-jobs`, `api-sync-status`, `api-sync-triggers`,
`api-tc-projects-management`) і є канонічними.

Під час доведення API до робочого стану (сесія 2026-06-12) додатково:

- **CLI-модуль `app/cli/`** з авто-реєстрацією команд (за зразком
  `dom-ex.bot`); перша команда — `add_user` (заводить `api_users` із
  bcrypt-хешем через `APIUserDAO.create_user`). Запуск:
  `python -m app.cli add_user` або `make add-user`. Це знімає попередню
  залежність від ручного `INSERT` першого користувача.
- **Хешування паролів переведено з `passlib` на прямий `bcrypt`**
  (`app/api/auth.py`) — `passlib` 1.7.4 несумісний із `bcrypt` 5.x на
  Python 3.14 (`decisinLog.md` → D-011). Формат хешу `$2b$` збережено,
  логін сумісний.
- **Python запінено на 3.14** через `.python-version` (узгоджено з
  `dom-ex.bot`); `requires-python` лишається `>=3.12,<4.0`.
- **`Makefile`** з шорткатами поверх `uv run`: `serve`, `dev`, `cli`,
  `add-user`, `sync`.

## Як це вписується в roadmap

`add-rest-api` — завершений етап 1 траєкторії з
[`projectbrief.md`](projectbrief.md). Наступні етапи (автоматичний
планувальник, власний трекер замість TimeCamp, multi-user масштаб) на
поточний код не впливають, але мотивували multi-user-ready вибори в
`decisinLog.md` → D-009. Незакомічена правка `main.ipynb` (період
`2026-04-08 .. 2026-04-13`) відображає експлуатаційний запуск, не нову
розробку.

## Нещодавні зміни (за git log)

- `bbb67bd` — оновлення залежностей та адаптація тасків.
- `6cc9094` — фікс типу колонки `created_at` для `jr_worklogs` (DateTime).
- `e94bed8` — реалізація створення worklog-ів у `Jira` через `Tempo`.
- `0384620` — додано стадію `before_create` для `WorllogSyncTask`.
- `eda6333` — основний сервіс `create_task_for_sync` + рефакторинг таблиць.

Ці зміни вже відображені в коді й моделях — окремих міграцій для них додавати
не потрібно (остання міграція — `b4117e0c3dd4`, 2024-10-02).

## Активні відкриті питання

- **Сценарій оновлення worklog-ів.** Статуси `pre_update/update/updated` в
  `StatusTaskEnum` зарезервовані, але не використовуються. Потрібно вирішити,
  коли і за яким триггером оновлювати раніше синхронізовані записи.
- **Назва `worllog_sync_task.py`.** Файл і клас містять одрук (`worllog` замість
  `worklog`). Перейменування зачепить імпорти — поки не виправлено
  (`decisinLog.md` → D-008).

## Найближчі кроки (як орієнтир для агентів)

1. Перед будь-якою правкою — прочитати всі файли в `docs/memory-bank/`.
2. Для нових міграцій — `alembic revision --autogenerate` після правки моделей
   (див. `techContext.md`).
3. Якщо змінюється логіка `BaseDAO._sync` — пам'ятати, що вона **видаляє**
   моделі, відсутні у DTO-списку (див. `systemPatterns.md`).

## Що ще не покрите Memory Bank

- Немає документації для веб-інтерфейсу/API (бо їх і не існує).
- Тестове покриття відсутнє; рішення про фреймворк тестів не прийняте.
