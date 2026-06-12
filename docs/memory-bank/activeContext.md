# Active Context

## Дата оновлення

2026-06-12 — реалізовано `restructure-monorepo-frontend` (до архівації).

## Поточний фокус

**Зміна
[`restructure-monorepo-frontend`](../../openspec/changes/restructure-monorepo-frontend/)
реалізована** (усі 47 тасків виконані; лишилось закомітити + заархівувати).
Що зроблено:

- **Бекенд переїхав `src/` → `api/app/`** (пакет перейменовано `src`→`app`,
  ~90 імпортів переписано). Smoke зелений: `from app.api.app import app`
  (24 роути), `python -m app.cli --help`, `alembic heads`/`current` =
  `ef2c7288bbb0`, `make dev` стартує і віддає `/healthz`. Усі бекенд-команди
  тепер із теки `api/` (кореневий `Makefile` робить `cd api && …`).
- **Env-фікс:** `app/config.py` резолвить env-файли **абсолютними** шляхами
  (cwd бекенду — `api/`), пріоритет за зростанням:
  `api/.env.template` (дефолти, перенесено сюди з кореня) → `<root>/.env`
  (спільний, його ж читає docker-compose) → `api/.env` (опційний локальний
  override, gitignore, не бакається в образ). Реальні env — над усіма;
  `env_ignore_empty=True`. Без цього `make dev` падав на
  `APP__API__JWT_SECRET is required`. Деталь — `design.md` D2.
- **Каркас `front/`** на Vue 3 + Vite + TypeScript: `vue-router`, **Pinia**,
  типізований **`fetch`**-клієнт (`VITE_API_BASE_URL`). `npm run build`
  (`vue-tsc --noEmit` + `vite build`) і dev-server `:5173` — перевірені.
- **Docker на корені, мультисервіс + dev hot-reload:** `api` (`./api`,
  `uvicorn --reload`, код-маунт, polling) + `front` (`./front`, Vite,
  polling) + `db`, спільна мережа `appnet`. Доступ через **host-nginx** на
  `http://sync.loc`/`https://sync.dev` (`docker/nginx.loc.conf`): `/` → Vite,
  `/api/` → бек. HMR за двома доменами — канонічний `wss://sync.dev`
  (env `VITE_HMR_*`, потрібен mkcert-cert). Гайд —
  `docs/technical/dev-environment.md`. Конфіги валідні (`vite build`,
  `docker compose config`); образи зібрані. End-to-end `up`+nginx — за
  користувачем (cert/домени + зупинка host-процесів).
- **Дворівневі інструкції:** кореневі `AGENTS.md`/`CLAUDE.md` — роутери;
  `api/` і `front/` мають власні з легкими вказівниками на скіли. Memory Bank
  оновлено (`techContext`, `systemPatterns`, `decisinLog` → D-012).

Доменна логіка, моделі та схема БД не змінювалися.

**Не перевірено в цій сесії (середовищне обмеження, не регресія):**
end-to-end `docker compose up` усього стека — щоб не чіпати вже підняті
9-денні контейнери (`tplfastapi_db_pgsql` на `11331`, той самий
`container_name`) і живу БД. Образи `api`/`front` зібрані, `compose config`
валідний; alembic уже конектиться до живої БД (head `ef2c7288bbb0`).

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
