## Why

Проект досі — single-repo Python-бекенд (`src/`), і `systemPatterns.md` уже
закладає шар "майбутній front", якого фізично немає. Roadmap
(`projectbrief.md`) веде до веб-інтерфейсу та multi-user, тож настав момент
підготувати інфраструктуру: розділити репо на `api/` і `front/`, дати
кожній частині власний стек і власні інструкції для агентів, та підняти
каркас веб-фронтенду на **Vue 3 + Vite + TypeScript**. Зробити це окремою
структурною зміною дешевше, ніж змішувати переїзд із продуктовими фічами.

## What Changes

- **BREAKING (для розробницького середовища):** Python-пакет переїжджає
  `src/` → `api/app/`. Усі ~90 імпортів `src.*` переписуються на `app.*`.
  Точки входу (`run_api.py`, `main.py`, `main.ipynb`), `migrations/`,
  `alembic.ini`, `pyproject.toml`, `uv.lock`, `.python-version`
  переїжджають у `api/`. CLI-запуск стає `python -m app.cli` (було
  `python -m src.cli`). `Makefile` лишається на корені як точка оркестрації
  монорепо (бекенд-цілі запускаються в `api/`).
- Створюється `front/` із робочим каркасом **Vue 3 + Vite + TypeScript**:
  `package.json`, `vite.config.ts`, `tsconfig.json`, `index.html`,
  `front/src/` (`App.vue`, базовий роутер, типізований HTTP-клієнт до REST
  API). Dev-сервер піднімається, продакшн-збірка проходить.
- Docker лишається на **верхньому рівні** (root), але стає мультисервісним:
  build context бекенду → `./api`, додається сервіс/`Dockerfile` для
  front. `.dockerignore`/`.gitignore` оновлюються під нові шляхи
  (`front/node_modules`, `front/dist`).
- Інструкції для агентів стають дворівневими: `docs/memory-bank/`,
  `openspec/` і загальні скіли (`.claude/skills`) лишаються **спільними** на
  корені; кореневі `AGENTS.md`/`CLAUDE.md` роутять у підтеки. `api/` і
  `front/` отримують власні `AGENTS.md`, `CLAUDE.md` і локальні скіли під
  свій стек (реалізовані як легкі вказівники, не `.claude/skills/`).
  **BREAKING для конвенції:** попереднє правило "скіли глобальні,
  локальних копій не тримаємо" свідомо переглядається — фіксується в
  `decisinLog.md`.
- `APP__API__CORS_ORIGINS` має дозволяти Vite dev-origin
  (`http://localhost:10332`).
- Доменна логіка, моделі та схема БД **не змінюються** — це чисто
  структурний/інфраструктурний рефактор плюс новий front-каркас.

## Capabilities

### New Capabilities
- `monorepo-layout`: канонічна структура монорепо — `api/` (пакет `app`)
  та `front/`, що́ лежить на корені як спільне, а що́ — per-folder; правила
  іменування пакета та точок входу після переїзду.
- `frontend-app`: каркас веб-застосунку на Vue 3 + Vite + TypeScript —
  dev-сервер, продакшн-збірка, маршрутизація, типізований HTTP-клієнт до REST
  API, конфіг бекенд-URL.
- `container-orchestration`: мультисервісний Docker на корені — build context
  бекенду `./api`, окремий front-сервіс, узгоджені ignore-файли та
  CORS під dev-origin.
- `workspace-conventions`: дворівнева розкладка інструкцій агентів —
  спільні Memory Bank/OpenSpec/загальні скіли на корені плюс per-folder
  `AGENTS.md`/`CLAUDE.md`/локальні скіли; роутинг із кореня в підтеки.

### Modified Capabilities
<!-- Поведінка наявних API-капабіліті (api-auth, api-jobs, api-sync-status,
     api-sync-triggers, api-tc-projects-management) НЕ змінюється — це
     структурний переїзд. Delta-специфікацій немає. -->

## Impact

- **Код:** усі `.py` у `src/` (переїзд + переписані імпорти `src.*` → `app.*`),
  `migrations/env.py` (`from app.config`, `from app.models`), `run_api.py`
  (`app.api.app:app`), `main.py`, ноутбуки (`main.ipynb`, `test.ipynb`,
  `sqla_test.ipynb`).
- **Конфіги/інфра:** `alembic.ini` (`prepend_sys_path`), `pyproject.toml`,
  `Makefile`, `Dockerfile`, `docker-compose.yml`, `.dockerignore`,
  `.gitignore`, `.env`/`.env.template` (CORS-origin).
- **Нове:** уся тека `front/`; `api/AGENTS.md`, `api/CLAUDE.md`,
  `front/AGENTS.md`, `front/CLAUDE.md` + локальні скіли.
- **Інструкції/доки:** кореневі `AGENTS.md`/`CLAUDE.md` (роутинг),
  `docs/memory-bank/techContext.md` (команди тепер з `api/`),
  `systemPatterns.md` (front-шар стає реальним), `decisinLog.md` (нове
  рішення про per-folder скіли).
- **Залежності/тулінг:** додається Node.js-тулчейн (Vite/Vue/TS) для front.
- **Не зачіпається:** доменні моделі, DAO, сервіси, схема БД, alembic head,
  REST-контракти.
