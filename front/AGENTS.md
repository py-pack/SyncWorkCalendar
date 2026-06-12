# AGENTS.md — `front/` (веб-фронтенд)

> Спершу прочитай кореневі `AGENTS.md` і `docs/memory-bank/`. Тут — лише
> нюанси фронтенду.

## Стек і запуск

- **Vue 3** (Composition API, `<script setup lang="ts">`) + **Vite** +
  **TypeScript**. Маршрутизація — `vue-router`, стейт — **Pinia**.
- HTTP-клієнт — рідний **`fetch`** (без `axios`), `src/api/client.ts`.
  Базовий URL — з `import.meta.env.VITE_API_BASE_URL` (не хардкодити!).
- Менеджер — `npm`. Команди виконуються **з теки `front/`**:
  - `npm install` — залежності.
  - `npm run dev` — Vite dev-server на `:5173`.
  - `npm run build` — перевірка типів (`vue-tsc --noEmit`) + продакшн-збірка.
  - `npm run preview` — прев'ю продакшн-збірки.
- Кореневі шорткати: `make front-dev`, `make front-build`.

## Структура

```
front/src/
  main.ts            # createApp + Pinia + router
  App.vue            # layout + <RouterView/>
  router/index.ts    # маршрути
  views/             # сторінки (HomeView.vue)
  stores/            # Pinia-store-и (health.ts — приклад)
  api/               # client.ts (fetch) + types.ts
```

## Робочі правила

- Звернення до бекенду — лише через `src/api/client.ts`; нові ендпойнти
  додавай типізованими методами + типами у `src/api/types.ts`.
- У dev фронт ходить в API через **Vite-проксі** (`/api` → бекенд), тож
  один origin і CORS не потрібен. Ціль проксі — `VITE_API_PROXY_TARGET`
  (`http://localhost:8000` локально, `http://api:8000` у docker-compose).
- Не комітити `.env` із секретами; `.env.development`/`.env.example` —
  тільки несекретні dev-дефолти.
- Бекенд-контракти (схеми відповідей) дивись у `api/app/api/schemas/`.

## Скіли (легкі вказівники)

- PHP-скіли (`phpstorm-plugin:*`) тут **не застосовні**.
- Документація — `technical-docs-writer`; Memory Bank — `memory-bank-manager`.
- Спеціалізованих Vue/TS-скілів у проекті немає — діємо за цим файлом і
  загальними.
