# container-orchestration Specification

## Purpose
TBD - created by archiving change restructure-monorepo-frontend. Update Purpose after archive.
## Requirements
### Requirement: Docker лишається на корені й стає мультисервісним

`Dockerfile`(и) та `docker-compose.yml` SHALL лишатися на верхньому рівні
репозиторію. `docker-compose.yml` SHALL описувати сервіси `db`, `api`
(бекенд) та front.

#### Scenario: Build context бекенду вказує на api/

- **WHEN** перевіряється сервіс `api` у `docker-compose.yml`
- **THEN** його build context — `./api`, а COPY-шляхи у Dockerfile
  узгоджені з тим, що `pyproject.toml`/`uv.lock` тепер у `api/`

#### Scenario: Бекенд-образ збирається після переїзду

- **WHEN** виконується `docker compose build api`
- **THEN** образ збирається без помилок (залежності й код знайдені у
  новому контексті)

#### Scenario: Front має власний сервіс у dev-режимі

- **WHEN** перевіряється `docker-compose.yml`
- **THEN** присутній окремий front-сервіс (Node/Vite) зі своїм build
  context `./front`, який у режимі розробки піднімає Vite dev-server
- **AND** усі три сервіси (`db`, `api`, `front`) перебувають у спільній
  compose-мережі

### Requirement: Коректне проксування API в dev-режимі

У режимі розробки front-сервіс SHALL проксувати запити до REST API на сервіс
`api` по compose-мережі, щоб у браузера був один origin і запити ходили
коректно між контейнерами без ручного налаштування CORS.

#### Scenario: Vite проксує API на сервіс api

- **WHEN** перевіряється `front/vite.config.ts`
- **THEN** `server.proxy` спрямовує API-префікс (напр. `/api`) на сервіс
  `api` по compose-мережі (напр. `http://api:10331`)

#### Scenario: Запит фронту в dev доходить до бекенду

- **WHEN** у піднятому `docker compose` (dev) фронтенд звертається до API
  через проксований префікс
- **THEN** запит доходить до сервісу `api` і не блокується CORS

### Requirement: Гаряче перезавантаження бекенду й фронтенду в dev

У dev-режимі docker-стек SHALL застосовувати зміни коду без ручного
перезапуску — і для бекенду, і для фронтенду.

#### Scenario: Бекенд перезавантажується на зміну коду

- **WHEN** піднято `docker compose` і змінюється `.py` під `api/app/`
- **THEN** сервіс `api` працює через `uvicorn --reload` із змонтованим кодом
  (`./api:/app`), а `.venv` береться з образу (анонімний том `/app/.venv`)
- **AND** reload надійно спрацьовує на bind-mount (`WATCHFILES_FORCE_POLLING`)

#### Scenario: Фронтенд застосовує зміни через HMR

- **WHEN** піднято `docker compose` і змінюється файл під `front/src/`
- **THEN** сервіс `front` працює через Vite dev-server із змонтованим кодом
  (`./front:/app`, `node_modules` — з образу) і застосовує зміну через HMR
- **AND** файлвотчинг надійний на bind-mount (`VITE_USE_POLLING`)

### Requirement: Маршрутизація через host-nginx на кастомних доменах

Проект SHALL надавати конфіг host-nginx, що віддає фронтенд і проксує API на
доменах `http://sync.loc` та `https://sync.dev`, із робочим HMR-websocket.

#### Scenario: Обидва домени віддають фронт і API

- **WHEN** host-nginx піднято з `docker/nginx.loc.conf`
- **THEN** на `sync.loc` і `sync.dev` `/` проксує на Vite (`127.0.0.1:10332`),
  а `/api/` — на бекенд (`127.0.0.1:10331`) зі зрізанням префікса `/api`

#### Scenario: HMR-websocket проходить через nginx

- **WHEN** браузер відкриває застосунок на кастомному домені
- **THEN** nginx проксує `Upgrade`/`Connection` для HMR-ws, а Vite
  налаштований на канонічний endpoint `wss://sync.dev` (env `VITE_HMR_*`),
  доступний і зі сторінки `sync.loc`, і `sync.dev`

#### Scenario: Запити не йдуть на внутрішні адреси

- **WHEN** застосунок звертається до API за `VITE_API_BASE_URL=/api`
- **THEN** запит відносний до origin домену й маршрутизується nginx-ом;
  внутрішні compose-адреси (`api:10331`) браузеру не експонуються

### Requirement: Ignore-файли узгоджені з новою структурою

`.gitignore` та `.dockerignore` SHALL відображати нову розкладку й виключати
артефакти front.

#### Scenario: Frontend-артефакти ігноруються

- **WHEN** перевіряються `.gitignore` і `.dockerignore`
- **THEN** вони містять `front/node_modules` та `front/dist`
- **AND** наявні правила (`.db/`, `.venv`) лишаються валідними для нових
  шляхів

### Requirement: CORS дозволяє front dev-origin

Бекенд SHALL приймати запити з Vite dev-origin під час локальної розробки.

#### Scenario: Vite origin дозволений

- **WHEN** `APP__API__CORS_ORIGINS` налаштовано для локальної розробки
- **THEN** воно включає `http://localhost:10332` (або `*`), і браузерний
  запит фронтенду до API не блокується CORS

### Requirement: Async-стек — сервіси `redis`, `worker`, `beat`

`docker-compose.yml` SHALL додатково описувати сервіси `redis` (брокер черги),
`worker` (Celery-воркер) і `beat` (Celery-планувальник), на додачу до наявних
`db`/`api`/`front`, у спільній compose-мережі.

- `redis` SHALL зберігати дані в **іменованому Docker volume** і публікувати
  host-порт за схемою `TT-AA-S` — **`11332`** (тип БД `11`, продукт `33`, індекс `2`).
- `worker` і `beat` SHALL використовувати той самий build context, що `api`
  (`./api`), і **не** публікувати портів; обидва залежать від `redis` і `db`.
- `beat` SHALL запускатись рівно в одному екземплярі.

#### Scenario: Compose описує async-стек

- **WHEN** перевіряється `docker-compose.yml`
- **THEN** присутні сервіси `redis`, `worker`, `beat`; `redis` має іменований volume
  і host-порт `11332`; `worker`/`beat` — без публікованих портів і в одній мережі з
  `api`/`db`

#### Scenario: Worker і beat бачать брокер і БД

- **WHEN** піднято `docker compose up`
- **THEN** `worker` і `beat` підключаються до `redis` (`APP__REDIS__URL`) і до `db`,
  а постановлені в чергу задачі виконуються воркером

