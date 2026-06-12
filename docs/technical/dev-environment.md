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
- Якщо змінив залежності — перебудуй і перествори томи:
  `docker compose up --build` (а за потреби `docker compose down -v`, бо
  `.venv`/`node_modules` живуть в анонімних томах і можуть застаріти).

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

## 7. Prod (поза скоупом)

Для продакшну фронт збирається у статику (`npm run build` → `front/dist`) і
роздається nginx-ом; dev Vite-сервер у проді не використовується. Це окрема
майбутня зміна.
