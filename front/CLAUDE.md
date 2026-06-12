# CLAUDE.md — `front/` (веб-фронтенд)

> Кореневий `CLAUDE.md` + `docs/memory-bank/` читаються першими. Тут — лише
> локальні нюанси фронту; повні правила — у [`AGENTS.md`](AGENTS.md).

## Швидкий старт

Усе виконується **з теки `front/`** (Vue 3 + Vite + TS, менеджер `npm`):

```sh
npm install        # залежності
npm run dev        # Vite dev-server :5173
npm run build      # vue-tsc --noEmit + vite build → dist/
```

Або кореневі шорткати: `make front-dev`, `make front-build`.

## Ключові застереження

- HTTP — лише `fetch` через `src/api/client.ts`; базовий URL із
  `import.meta.env.VITE_API_BASE_URL` (не хардкодити). Без `axios`.
- Стейт — Pinia (`src/stores/`); приклад — `health.ts`.
- У dev API проксується Vite (`/api` → бекенд), тож CORS не потрібен; ціль —
  `VITE_API_PROXY_TARGET`.
- `.env` із секретами не комітити.

## Скіли (легкі вказівники)

`technical-docs-writer` (тех-доки), `memory-bank-manager` (Memory Bank).
PHP-скіли не застосовні. Окремих Vue/TS-скілів немає.
