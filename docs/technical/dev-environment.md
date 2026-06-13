# Dev-середовище: Docker + host-nginx + HMR

Локальна розробка з гарячим перезавантаженням бекенду й фронтенду, доступ
через кастомні домени `http://sync.loc` та `https://sync.dev`.

## Топологія

```
Браузер
  → host-nginx (sync.loc:80 / sync.dev:443)
       ├─ /        → Vite dev-server  127.0.0.1:10332  (+ HMR websocket)
       └─ /api/    → FastAPI backend  127.0.0.1:10331  (префікс /api зрізається)
```

Host-порти за конвенцією (щоб проекти не конфліктували): **10xxx — сервіси**
(api `10331`, front `10332`), **11xxx — БД** (postgres `11331`). `:10331` і
`:10332` однаково слухає localhost, тож nginx-конфіг той самий незалежно від
того, де крутяться сервіси — у docker-compose чи на хості.

## 1. Домени (/etc/hosts)

```
127.0.0.1  sync.loc sync.dev
```

## 2. Cert для https://sync.dev (mkcert — локально довірений)

```sh
brew install mkcert nss
mkcert -install
mkdir -p /opt/homebrew/etc/nginx/certs
cd /opt/homebrew/etc/nginx/certs
mkcert sync.dev          # → sync.dev.pem + sync.dev-key.pem
```

## 3. nginx

Конфіг — [`docker/nginx.loc.conf`](../../docker/nginx.loc.conf). Поклади/злінкуй
у каталог, який Homebrew nginx включає в `http{}`:

```sh
ln -sf "$PWD/docker/nginx.loc.conf" /opt/homebrew/etc/nginx/servers/sync.conf
nginx -t && nginx -s reload          # або: brew services restart nginx
```

(Шляхи до cert у `sync.conf` за потреби підправ під свої.)

## 4. Запуск сервісів

### Варіант A — усе в docker (full stack)

```sh
docker compose up           # api (uvicorn --reload) + front (vite) + db
```

- Бекенд: `uvicorn … --reload`, код змонтований (`./api:/app`), `.venv` —
  з образу (анонімний том `/app/.venv`), reload через polling
  (`WATCHFILES_FORCE_POLLING=true`).
- Фронт: `vite --host`, код змонтований (`./front:/app`), `node_modules` — з
  образу, файлвотчинг через polling (`VITE_USE_POLLING=true`).
- **Зміна залежностей — пастка анонімних томів.** `.venv` (api) і
  `node_modules` (front) живуть в анонімних томах (`/app/.venv`,
  `/app/node_modules`), які **перекривають** свіжий вміст образу і **не
  оновлюються** від простого `docker compose up --build`. Симптом: застосунок
  падає на старті з `ModuleNotFoundError` (напр. `No module named 'google'`
  після додавання `google-auth`), хоча залежність уже в `pyproject.toml`/
  `uv.lock`. Лагодити одним із:
  - швидко, без ребілду: `docker compose exec api uv sync --frozen --no-dev`
    (front — `docker compose exec front npm ci`), далі
    `docker compose restart <svc>`;
  - чисто, перезалити том із образу:
    `docker compose up -d --build --renew-anon-volumes <svc>`.

  Просто `--build` **не** перезаливає анонімний том — це і є пастка.

### Варіант B — front+back на хості, db у docker (найлегший HMR)

```sh
docker compose up -d db
make dev            # бекенд: uvicorn --reload (:10331), нативний reload
make front-dev      # фронт: vite (:10332), нативний файлвотчинг
```

## 5. HMR за кастомними доменами

Один Vite-інстанс не може віддавати HMR-websocket одночасно на `http:80` і
`https:443` (mixed-content: https-сторінка приймає лише `wss`). Тому
**канонічний HMR-endpoint — `wss://sync.dev`**: туди під'єднуються і сторінка
`sync.dev`, і `sync.loc` (secure-ws з http-сторінки дозволено браузером). Для
цього `sync.dev` має бути піднятий і його cert — довірений (див. крок 2).

Налаштовується **двома** env (у docker-compose вже задано) — домен + чи https;
`protocol` (wss/ws) і `clientPort` (443/80) виводяться автоматично:

```
VITE_HMR_HOST=sync.dev  VITE_HMR_HTTPS=true
```

Якщо працюєш переважно на http-домені `sync.loc` — перемкни:
`VITE_HMR_HOST=sync.loc VITE_HMR_HTTPS=false`
(тоді https-сторінка `sync.dev` HMR не отримає через mixed-content). За потреби
можна перевизначити явно: `VITE_HMR_PROTOCOL`, `VITE_HMR_CLIENT_PORT`.

Прямий доступ `http://localhost:10332` (без nginx) працює з HMR за
замовчуванням — просто не задавай `VITE_HMR_*`.

## 6. Чому запити не «летять у внутрішню мережу»

`VITE_API_BASE_URL=/api` — **відносний**. Браузер бачить тільки
`sync.loc`/`sync.dev`; запит `/api/...` ловить nginx і проксує на бекенд.
Внутрішні адреси (`api:10331`) браузеру не світяться. Vite-проксі (`/api` →
`VITE_API_PROXY_TARGET`) — лише фолбек для прямого доступу `:10332` без nginx.

## 7. Google-вхід: client_id у фронт-контейнер

Публічний `VITE_GOOGLE_CLIENT_ID` фронт читає лише зі своїх `front/.env*` або з
`process.env` контейнера — **не** з кореневого `.env` (Vite дивиться в теку
`front/`, root `.env` йому невидимий). Тому в `docker-compose.yml` змінна
**прокидається** у front-сервіс із root `.env`:

```yaml
environment:
  VITE_GOOGLE_CLIENT_ID: ${VITE_GOOGLE_CLIENT_ID:-}
```

`process.env` має пріоритет над `front/.env*`, тож порожнє значення у файлі не
заважає. Після зміни — `docker compose up -d front` (саме `up`, бо змінюється
`environment`, а не лише код). Бек бере свій `APP__API__GOOGLE_CLIENT_ID`/
`GOOGLE_CLIENT_SECRET` із root `.env` через `env_file`. Authorized JS origin для
Google Console — `https://sync.dev` (без redirect URI: popup-флоу шле
`redirect_uri=postmessage`). Деталі рішень — Memory Bank `decisinLog.md`
→ D-013 (Google-вхід), D-014 (front HTTP-клієнт).

## 8. Prod (поза скоупом)

Для продакшну фронт збирається у статику (`npm run build` → `front/dist`) і
роздається nginx-ом; dev Vite-сервер у проді не використовується. Це окрема
майбутня зміна.
