# frontend-app Specification

## Purpose
TBD - created by archiving change restructure-monorepo-frontend. Update Purpose after archive.
## Requirements
### Requirement: Каркас Vue 3 + Vite + TypeScript

Тека `front/` SHALL містити робочий застосунок на **Vue 3** із
**Vite**-збіркою та **TypeScript**. Конфігурація SHALL включати
`package.json`, `vite.config.ts`, `tsconfig.json`, `index.html` та
`front/src/` із кореневим компонентом `App.vue`.

#### Scenario: Залежності встановлюються

- **WHEN** у `front/` виконується `npm install`
- **THEN** залежності встановлюються без помилок, з'являється
  `front/node_modules`

#### Scenario: Продакшн-збірка проходить

- **WHEN** у `front/` виконується `npm run build`
- **THEN** збірка завершується успішно і генерується `front/dist`
- **AND** перевірка типів TypeScript не падає

#### Scenario: Dev-сервер піднімається

- **WHEN** у `front/` виконується `npm run dev`
- **THEN** Vite піднімає dev-сервер на `http://localhost:10332` і віддає
  кореневий компонент `App.vue`

### Requirement: Маршрутизація на стороні клієнта

Фронтенд SHALL мати налаштований клієнтський роутер (`vue-router`) щонайменше
з одним маршрутом, який рендериться через `App.vue`.

#### Scenario: Кореневий маршрут рендериться

- **WHEN** користувач відкриває `/` у dev-режимі
- **THEN** роутер монтує стартову сторінку без помилок у консолі

### Requirement: Типізований HTTP-клієнт до REST API на `fetch`

Фронтенд SHALL містити типізований HTTP-клієнт для звернень до бекенд REST
API на основі рідного **`fetch`** (без зовнішніх HTTP-залежностей на кшталт
`axios`). Базовий URL API SHALL братися з конфігурації середовища (Vite env),
а не бути захардкодженим.

#### Scenario: Базовий URL конфігурований

- **WHEN** змінюється `VITE_API_BASE_URL` (env)
- **THEN** HTTP-клієнт використовує нове значення без правок коду

#### Scenario: Клієнт типізований

- **WHEN** виконується перевірка типів збірки
- **THEN** методи HTTP-клієнта мають типи запиту/відповіді (а не `any`)

#### Scenario: Без зовнішньої HTTP-залежності

- **WHEN** перевіряється `front/package.json`
- **THEN** `axios` (чи аналогічний HTTP-клієнт) у залежностях відсутній —
  клієнт побудовано на `fetch`

### Requirement: Стейт-менеджер Pinia

Фронтенд SHALL мати підключений **Pinia** із щонайменше одним базовим store,
щоб перша реальна в'юха мала готовий store-каркас.

#### Scenario: Pinia підключено

- **WHEN** перевіряється `front/package.json` і точка входу `main.ts`
- **THEN** `pinia` присутній у залежностях і реєструється у Vue-застосунку
- **AND** існує щонайменше один store у `front/src/`

