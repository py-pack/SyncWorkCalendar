## 1. Перенос бекенду у `api/` (git mv)

- [x] 1.1 `git mv src api/app` — перенести пакет і перейменувати його в `app`
- [x] 1.2 `git mv` для `migrations/`, `alembic.ini`, `pyproject.toml`, `uv.lock`, `.python-version`, `run_api.py`, `main.py` у `api/` (`Makefile` НЕ переносити — лишається на корені)
- [x] 1.3 Перенести ноутбуки (`main.ipynb`, `test.ipynb`, `sqla_test.ipynb`) у `api/`
- [x] 1.4 Перевірити, що на корені не лишилось бекенд-файлів (крім Docker, `Makefile` та спільних docs/openspec)
- [x] 1.5 Коміт — за рішенням користувача лишено незакоміченим (окремого move-коміту не робимо; move+rewrite в одному робочому дереві, фінальний коміт за користувачем)

## 2. Переписування імпортів `src.*` → `app.*`

- [x] 2.1 Замінити `from src` / `import src` / `src.` → `app` у всіх `.py` під `api/app/`
- [x] 2.2 Оновити `api/run_api.py` (`uvicorn.run("app.api.app:app")`) та докстрінг
- [x] 2.3 Оновити `api/main.py` (`from app.config`, `from app.services...`, `from app.dao...`, `from app.core...`)
- [x] 2.4 Оновити `api/migrations/env.py` (`from app.config import settings`, `from app.models import Base`)
- [x] 2.5 Оновити імпорти в ноутбуках (`src.*` → `app.*`)
- [x] 2.6 Оновити кореневий `Makefile` — бекенд-цілі запускаються в `api/` (`cd api && uv run python -m app.cli`, `cd api && uv run uvicorn app.api.app:app`, тощо)
- [x] 2.7 Звірити `alembic.ini` (`prepend_sys_path = .` лишається; шлях `script_location = migrations`)
- [x] 2.8 Контроль: `grep -rn "src\." api --include='*.py'` → нуль збігів

## 3. Smoke-перевірка бекенду

- [x] 3.1 `cd api && uv sync` — оточення піднімається з нового шляху
- [x] 3.2 `uv run python -c "from app.api.app import app; print(len(app.routes))"` — імпорт без помилок
- [x] 3.3 `uv run python -m app.cli --help` — CLI відповідає під новим пакетом
- [x] 3.4 `uv run alembic heads` — head лишається `ef2c7288bbb0`
- [x] 3.5 `uv run alembic upgrade head` на чистій БД — `env.py` резолвить `app.models`
- [x] 3.6 `make serve` / `uv run run_api.py` — API стартує (потрібен `APP__API__JWT_SECRET`)

## 4. Каркас фронтенду (Vue 3 + Vite + TypeScript)

- [x] 4.1 Згенерувати `front/` (Vue 3 + Vite + TS): `package.json`, `vite.config.ts`, `tsconfig.json`, `index.html`, `front/src/App.vue`, `main.ts`
- [x] 4.2 Додати `vue-router` із щонайменше одним маршрутом, що рендериться через `App.vue`
- [x] 4.3 Підключити **Pinia** у `main.ts` і завести щонайменше один базовий store у `front/src/`
- [x] 4.4 Додати типізований HTTP-клієнт на `fetch` (без `axios`) з базовим URL із `import.meta.env.VITE_API_BASE_URL`
- [x] 4.5 Налаштувати `server.proxy` у `vite.config.ts` — проксувати API-префікс (напр. `/api`) на сервіс `api` (`http://api:10331` у compose; `localhost:10331` локально)
- [x] 4.6 Додати `front/.env.example` (або `.env.development`) з `VITE_API_BASE_URL`
- [x] 4.7 `cd front && npm install && npm run build` — збірка + перевірка типів проходять, з'являється `front/dist`
- [x] 4.8 `npm run dev` — Vite піднімає dev-сервер на `:10332` і віддає `App.vue`

## 5. Docker на корені (мультисервіс)

- [x] 5.1 Перенести api `Dockerfile` у `api/` і узгодити `COPY`-шляхи (контекст тепер `./api`)
- [x] 5.2 Оновити `docker-compose.yml`: сервіс `api` → `build.context: ./api`
- [x] 5.3 Додати front `Dockerfile` (Node + Vite, **dev-режим**: Vite dev-server) та front-сервіс у `docker-compose.yml` (`build.context: ./front`)
- [x] 5.4 Звести `db`, `api`, `front` у спільну compose-мережу; переконатися, що dev-проксі (4.5) добивається до `api` по імені сервісу
- [x] 5.5 Оновити `.dockerignore` під нові шляхи (+ `front/node_modules`, `front/dist`)
- [x] 5.6 Оновити `.gitignore` (+ `front/node_modules`, `front/dist`; звірити `.db/`, `.venv`)
- [x] 5.7 Додати/оновити `APP__API__CORS_ORIGINS` у `.env.template` (включити `http://localhost:10332`) — запасний шлях для прямих звернень повз проксі
- [x] 5.8 `docker compose build api` та збірка front-сервісу проходять; `docker compose up` (dev) — фронт ходить в API через проксі

## 6. Інструкції агентів та скіли (дворівнево)

- [x] 6.1 Переписати кореневі `AGENTS.md`/`CLAUDE.md` на тонкі роутери (Memory Bank → `api/`/`front/`); прибрати застаріле правило "локальних скілів не тримаємо"
- [x] 6.2 Створити `api/AGENTS.md` + `api/CLAUDE.md` (Python/`uv`/Alembic/FastAPI-нюанси)
- [x] 6.3 Створити `front/AGENTS.md` + `front/CLAUDE.md` (Vue/TypeScript/Vite-нюанси)
- [x] 6.4 Додати в per-folder `AGENTS.md`/`CLAUDE.md` **легкі вказівники** на релевантні глобальні скіли + стек-специфіку (без `.claude/skills/` у підтеках)
- [x] 6.5 Звірити, що загальні скіли, `docs/memory-bank/`, `docs/technical/`, `openspec/` лишаються спільними на корені

## 7. Синхронізація Memory Bank і документації

- [x] 7.1 Оновити `techContext.md` — команди тепер виконуються з `api/`; додати front-тулчейн (Node/Vite)
- [x] 7.2 Оновити `systemPatterns.md` — front-шар став реальним; описати нову розкладку монорепо
- [x] 7.3 Додати запис у `decisinLog.md` — рішення про переїзд `src`→`app` та перегляд правила про per-folder локальні скіли
- [x] 7.4 Оновити `activeContext.md`/`progress.md` за фактом виконання
- [x] 7.5 Звірити, що відносні посилання в Memory Bank на `docs/technical/*` та `openspec/*` лишаються валідними

## 8. Фінальна валідація

- [x] 8.1 `openspec validate restructure-monorepo-frontend --strict` — без помилок
- [x] 8.2 Повторний прогін smoke (бекенд import + CLI + alembic + front build + docker build) — усе зелене

## 9. Dev hot-reload + host-nginx (кастомні домени)

- [x] 9.1 `docker-compose.yml`: `api` → `uvicorn --reload`, монтування `./api:/app` + анонімний `/app/.venv`, `WATCHFILES_FORCE_POLLING=true`
- [x] 9.2 `docker-compose.yml`: `front` → vite `--host`, `VITE_USE_POLLING=true`, HMR-env у 2 змінні (`VITE_HMR_HOST=sync.dev` + `VITE_HMR_HTTPS=true`; protocol/clientPort виводяться, override опційний)
- [x] 9.3 `vite.config.ts`: `allowedHosts` (sync.loc/sync.dev/localhost), `watch.usePolling` (env), `hmr` (env), збережено `proxy`
- [x] 9.4 Конфіг host-nginx `docker/nginx.loc.conf` — обидва домени → Vite (`/`, з HMR-ws) + бекенд (`/api/`, зрізання префікса), редірект http→https для sync.dev
- [x] 9.5 Гайд `docs/technical/dev-environment.md` — /etc/hosts, mkcert, nginx, запуск (docker full-stack / host), HMR-нюанс двох доменів
- [x] 9.6 Валідація: `vite build` (конфіг вантажиться) + `docker compose config -q` — OK
- [x] 9.7 End-to-end запуск підтверджено користувачем (стек піднявся, домени/HMR працюють)

## 10. Конвенція host-портів (щоб проекти не конфліктували)

- [x] 10.1 Застосувати схему `10xxx`=сервіси / `11xxx`=БД: api `10331`, front `10332`, db `11331`
- [x] 10.2 `docker-compose.yml`: публікація `${API_HOST_PORT:-10331}`, `${FRONT_HOST_PORT:-10332}`, `${DB_HOST_PORT:-11331}`; внутрішні порти/команди узгоджені
- [x] 10.3 Бекенд: `config.py` (`APIConfig.port=10331`), `api/.env.template` (`APP__API__PORT=10331`), `Dockerfile` (`EXPOSE 10331`)
- [x] 10.4 Фронт: `vite.config.ts` (`server.port=10332`, проксі-ціль `:10331`), env-файли
- [x] 10.5 `Makefile` (`API_PORT`/`FRONT_PORT`) та `docker/nginx.loc.conf` (апстріми `:10331`/`:10332`)
- [x] 10.6 Задокументувати конвенцію: скіл `preferred-docker-images` (`references/port-allocation.md`), Memory Bank (`techContext`), dev-гайд
