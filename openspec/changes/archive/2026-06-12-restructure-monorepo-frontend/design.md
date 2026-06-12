## Context

Репозиторій — single-repo Python-бекенд (`src/`: `api`, `dao`, `models`,
`services`, `tasks`, `cli`, `core`, `utils`, `config.py`). Точки входу:
`run_api.py`, `main.py`, `main.ipynb`. Інфра: `migrations/` + `alembic.ini`,
`pyproject.toml` + `uv.lock` (менеджер — `uv`), `Dockerfile` +
`docker-compose.yml` на корені. Project-wide контекст — у `docs/memory-bank/`
(канонічний) та `docs/technical/`; робочий процес — під OpenSpec
(`openspec/`).

`systemPatterns.md` уже малює шар "майбутній front", якого немає. Roadmap
у `projectbrief.md` (web UI, multi-user) робить розділення на `api/` і
`front/` природним наступним кроком. Це структурна зміна перед
продуктовими фічами.

Ключова механіка масштабу: **~90 згадок `src.`** у 35 `.py`-файлах, плюс
`migrations/env.py` (`from src.config`, `from src.models import Base`),
`run_api.py` (`src.api.app:app`), `main.py`, три ноутбуки, `Makefile`
(`python -m src.cli`, `src.api.app:app`), `alembic.ini`
(`prepend_sys_path = .`) і `Dockerfile` (`COPY . .`).

## Goals / Non-Goals

**Goals:**
- Перенести бекенд у `api/` і перейменувати пакет `src` → `app` з повним
  переписуванням імпортів.
- Підняти робочий каркас `front/` на Vue 3 + Vite + TypeScript (dev +
  build).
- Зберегти Docker на корені, зробивши його мультисервісним із коректними
  build-контекстами.
- Дати `api/` і `front/` власні `AGENTS.md`/`CLAUDE.md` та локальні
  скіли; спільний контекст лишити на корені.
- Не зламати наявну поведінку: API-контракти, доменна логіка, схема БД,
  alembic head — без змін.

**Non-Goals:**
- Жодних продуктових фіч у фронтенді (реальні сторінки/в'юхи поза каркасом).
- Жодних змін доменної логіки, моделей, DAO, схеми БД чи REST-контрактів.
- Жодної нової alembic-ревізії в межах цієї зміни.
- Не виправляємо наявні тех-борги (typo `worllog`, баг `JiraService`,
  `deprecated DatabaseHelper`) — це окремі зміни.
- Не налаштовуємо CI/тести (їх і так немає).

## Decisions

### D1 — Перейменувати пакет `src` → `app` (а не лишати `src` під `api/`)

**Рішення:** пакет переїжджає `src/` → `api/app/`, усі імпорти `src.*`
переписуються на `app.*`.

**Чому:** користувач явно обрав чисту довгострокову назву замість
найдешевшого шляху. `app` — конвенційне ім'я кореневого пакета FastAPI-сервісу
і прибирає вічну двозначність "`src` чого саме" в монорепо, де є ще
`front/src`.

**Альтернатива (відкинуто):** лишити пакет `src` усередині `api/`
(`api/src/`) — ~0 правок імпортів, але закріплює неінформативну назву й
плутає з `front/src`.

**Наслідки:** масовий, але механічний rewrite. Виконувати скриптовано
(`grep`-driven sed по `from src` / `import src` / `src.`), і обов'язково
звіряти контрольним `grep -rn "src\." api --include='*.py'` → нуль.

### D2 — `uv run` усе з робочою текою `api/`

**Рішення:** після переїзду всі бекенд-команди виконуються з `api/`:
`pyproject.toml`, `uv.lock`, `.venv`, `alembic.ini` живуть там. `alembic.ini`
лишає `prepend_sys_path = .` (тепер це `api/`). `run_api.py` піднімає
`app.api.app:app`. `migrations/env.py` бере `from app.config` / `from
app.models`.

**Чому:** пакет `app` резолвиться без зайвих `PYTHONPATH`-хаків, бо cwd —
корінь пакета. Мінімум магії.

**Env-файли:** `app/config.py` резолвить env-файли **абсолютними** шляхами
(бо cwd бекенду — `api/`), із пріоритетом за зростанням (пізніші перекривають
раніші; реальні OS/compose env — над усіма):

1. `api/.env.template` — бекендні дефолти (комітиться; `.env.template`
   перенесено сюди з кореня, бо це суто бекендні змінні).
2. `<root>/.env` — спільний конфіг; його ж використовує `docker-compose.yml`
   (`env_file` + інтерполяція `${APP__…}` для `db`), тож лишається на корені.
3. `api/.env` — опційний локальний override розробника (у `.gitignore`,
   у Docker-образ не бакається через `api/.dockerignore`).

`env_ignore_empty=True` — порожні значення з шаблону не затирають реальні.
Альтернатива (повний спліт env у `api/` з відмовою від root `.env`) відкинута
— тягне `--env-file ./api/.env` у кожен виклик compose.

**Наслідки:** `Makefile` **лишається на корені** (нікуди не переїжджає) — це
єдина точка оркестрації монорепо, куди згодом підуть і frontend-цілі. Його
наявні бекенд-цілі (`serve`, `dev`, `cli`, `add-user`, `sync`) переписуються
на запуск усередині `api/` (`cd api && uv run …`). `techContext.md` →
бекенд-команди тепер виконуються з `api/`, але шорткати `make …` лишаються
кореневими.

### D3 — Frontend: Vite-scaffold Vue 3 + TS, `fetch`-клієнт, Pinia

**Рішення:** каркас на офіційному Vue 3 + Vite + TypeScript template;
`vue-router` для маршрутизації; **Pinia** як стейт-менеджер (заводимо каркас
одразу); тонкий типізований HTTP-клієнт на **`fetch`** (без зовнішньої
залежності) із базовим URL з `import.meta.env.VITE_API_BASE_URL`.

**Чому:** Vite — дефолт для нового Vue+TS; env-конфіг URL потрібен, бо
бекенд-origin відрізняється в dev і в Docker. `fetch` обрано замість `axios` —
вистачає рідного API, мінус одна залежність. Pinia заводимо зараз, щоб перша
реальна в'юха вже мала готовий store-каркас і не тягла рефактор.

**Альтернатива (відкинуто):** `axios` — зайва залежність для нашого обсягу;
Nuxt/SSR — overkill для внутрішнього SPA поверх наявного REST API.

### D4 — Docker на корені, build-контексти в підтеки, dev-проксі

**Рішення:** `docker-compose.yml` лишається на корені; сервіс `api` отримує
`build.context: ./api`, окремий front-сервіс — `build.context: ./front`.
Backend `Dockerfile` переїжджає у `api/` (його `COPY pyproject.toml uv.lock
./` і `COPY . .` тепер відносні до `api/`). Front дістає власний `Dockerfile`.
Усі три сервіси (`db`, `api`, `front`) у спільній compose-мережі.

**Режим розробки — hot-reload обох сервісів:**
- `api`: `command: uvicorn … --reload`, код змонтований (`./api:/app`), а
  `.venv` береться з образу через **анонімний том** `/app/.venv` (host-`.venv`
  — macOS-arch, у linux-контейнері несумісний). Reload на bind-mount —
  `WATCHFILES_FORCE_POLLING=true` (inotify з macOS не пробивається).
- `front`: Vite dev-server (`--host`), код змонтований (`./front:/app`),
  `node_modules` — з образу (анонімний том). Файлвотчинг —
  `VITE_USE_POLLING=true`.

**Маршрутизація через host-nginx (кастомні домени):** браузерний доступ —
через nginx на хості на `http://sync.loc` і `https://sync.dev`; nginx віддає
`/` на Vite (`127.0.0.1:10332`) і `/api/` на бекенд (`127.0.0.1:10331`,
зрізає префікс). `VITE_API_BASE_URL=/api` лишається **відносним** — браузеру
не світяться внутрішні адреси (`api:10331`). Vite `server.proxy` лишається
фолбеком для прямого `:10332`. Конфіг — `docker/nginx.loc.conf`, гайд —
`docs/technical/dev-environment.md`.

**Конвенція host-портів** (щоб проекти не конфліктували між собою): `10xxx` —
сервіси (api `10331`, front `10332`), `11xxx` — БД (postgres `11331`). Той
самий host-порт у docker (публікація) і на хості (`make dev`/`front-dev`), тож
nginx-апстріми незмінні.

**HMR за двома доменами:** один Vite не може віддавати HMR-ws і на `http:80`,
і на `https:443` (mixed-content: https-сторінка приймає лише `wss`). Тому
**канонічний endpoint — `wss://sync.dev`**, що обслуговує і `sync.loc`, і
`sync.dev`. Задається двома env — `VITE_HMR_HOST` (домен) + `VITE_HMR_HTTPS`
(true/false); `protocol`/`clientPort` виводяться (явний override опційний).
Vite `allowedHosts` включає обидва домени. Потрібен довірений cert `sync.dev`
(mkcert).

**Чому:** компоуз-оркестрація project-wide (зв'язує `db`+`api`+`front`), тож
на корені. Host-nginx дає реалістичний single-origin dev на доменах і прибирає
CORS; внутрішні адреси не експонуються.

**Наслідки:** `.dockerignore` під нові шляхи; CORS під `:10332`/домени —
фолбек для прямих звернень повз nginx. **Prod-раздача статики (build + nginx)** —
поза скоупом (dev використовує Vite dev-server), окрема майбутня зміна.

### D5 — Дворівневі інструкції; локальні скіли як легкі вказівники

**Рішення:** Memory Bank, OpenSpec і загальні скіли лишаються спільними на
корені; кореневі `AGENTS.md`/`CLAUDE.md` стають тонкими роутерами ("читай
Memory Bank → іди в `api/` або `front/`"). Кожна підтека дістає власні
`AGENTS.md`/`CLAUDE.md`. Локальні скіли per-folder реалізуємо як **легкі
вказівники** (короткі нотатки/посилання у відповідних `AGENTS.md`/`CLAUDE.md`
на потрібні глобальні скіли + стек-специфіка), а не повноцінні директорії
`.claude/skills/` усередині `api/`/`front/`.

**Чому:** користувач явно цього хоче. Легкі вказівники дають per-folder
орієнтацію без дублювання й підтримки повноцінних скіл-пакетів у кожній теці.
Це свідомо **скасовує** попереднє правило ("скіли глобальні, локальних копій
не тримаємо" з `AGENTS.md`).

**Наслідки:** додати запис у `decisinLog.md` (нове рішення про per-folder
вказівники із причиною); оновити кореневі `AGENTS.md`/`CLAUDE.md`, щоб вони
більше не стверджували протилежне. Якщо згодом знадобляться повноцінні
локальні скіли — це окрема майбутня зміна.

## Risks / Trade-offs

- **Пропущений `src.`-імпорт → runtime ImportError.** → Контрольний
  `grep -rn "src\." api --include='*.py'` має давати нуль; обов'язкові
  smoke-перевірки: `uv run python -c "from app.api.app import app"`,
  `uv run python -m app.cli --help`.
- **Alembic втратить metadata / env.py зламається.** → Після переїзду
  `uv run alembic heads` (має лишитись `ef2c7288bbb0`) і
  `uv run alembic upgrade head` на чистій БД як перевірка, що `env.py`
  резолвить `from app.models import Base`.
- **Docker COPY-шляхи розійдуться з новим контекстом → битий образ.** →
  `docker compose build api` як приймальний крок; те саме для front.
- **Ноутбуки (`main.ipynb` та ін.) лишаться зі старими `src.`-імпортами.** →
  Оновити імпорти в ноутбуках або явно задокументувати в `techContext.md`,
  що їх запускати з `api/`. Незакомічену правку періоду в `main.ipynb`
  не чіпати по суті.
- **Битий git-history blame через масовий move.** → Переносити через
  `git mv` (зберігає історію краще, ніж delete+add); імпорт-rewrite окремим
  комітом від move.
- **CORS заблокує фронтенд у dev.** → За nginx фронт і API — один origin
  (CORS не потрібен). Для прямого доступу `:10332` — `APP__API__CORS_ORIGINS`
  лишається `*`/включає `http://localhost:10332`.
- **Розсинхрон Memory Bank.** → Оновити `techContext.md` (команди з
  `api/`), `systemPatterns.md` (front-шар став реальним),
  `decisinLog.md`; синк робиться в межах apply/archive.

## Migration Plan

1. **Перенос у `api/`** (один комміт): `git mv src api/app`; перенести
   `migrations/`, `alembic.ini`, `pyproject.toml`, `uv.lock`,
   `.python-version`, `run_api.py`, `main.py`, ноутбуки у `api/`.
   `Makefile` **лишається на корені**.
2. **Import rewrite** (окремий комміт): `src.` → `app.` усюди + `run_api.py`,
   `migrations/env.py`. Кореневий `Makefile` — бекенд-цілі на `cd api && …`.
   Контрольний grep → нуль. Smoke: import app, CLI help, alembic heads/upgrade.
3. **Frontend scaffold**: `front/` із Vue 3 + Vite + TS, роутер,
   HTTP-клієнт; `npm install && npm run build` проходить.
4. **Docker + ignore + CORS**: контексти `./api` і `./front`, front
   `Dockerfile`, `.dockerignore`/`.gitignore`, CORS-origin. `docker compose
   build` обох сервісів.
5. **Інструкції/доки**: кореневі `AGENTS.md`/`CLAUDE.md` → роутери; per-folder
   `AGENTS.md`/`CLAUDE.md` + локальні скіли; оновити Memory Bank і
   `decisinLog.md`.

**Rollback:** зміна структурна й ізольована від доменної логіки — відкат =
`git revert` коммітів move + rewrite; БД і схема не зачіпаються, тож
data-міграція для відкату не потрібна.

## Open Questions

Усі попередні відкриті питання закриті (рішення зафіксовані в D3–D5):

- HTTP-клієнт фронтенду — **`fetch`** (без `axios`). → D3.
- Стейт-менеджмент — **Pinia, заводимо каркас одразу**. → D3.
- Front-сервіс у Docker — **dev-режим (Vite dev-server) з проксуванням** на
  сервіс `api` по compose-мережі; продакшн-раздача статики поза скоупом. → D4.
- Формат локальних скілів per-folder — **легкі вказівники** в
  `AGENTS.md`/`CLAUDE.md`, без повноцінних `.claude/skills/` у підтеках. → D5.

Лишається на etап реалізації (не блокери): фінальний продакшн-варіант
раздачі статики фронту (nginx vs build-артефакт) — вирішимо з першими
реальними сторінками.
