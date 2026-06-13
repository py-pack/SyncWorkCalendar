## 1. Компонент `DataPage`

- [x] 1.1 Створити `front/src/components/data/DataPage.vue`: props `title:
  string` (required), `desc?: string`, `error?: string | null`; слоти
  `#actions` (верхній правий кут), `#toolbar` (опційний суб-бар), default (тіло
  в `.page__body`). Поглинути розмітку `PageHeader` (title/desc/`#actions`) і
  банер `data-error` (іконка `alert`, рендер лише при непорожньому `error`).
  Переюз наявних класів `styles/shell.css` (`.page`/`.page__head`/`.page__titles`/
  `.page__actions`/`.page__body`).
- [x] 1.2 **Закладки:** додати props `tabs?: TabItem[]` + `activeTab?: string` і
  подію `update:activeTab` (підтримка `v-model:active-tab`); коли `tabs` задано —
  рендерити наявний `Tabs` під заголовком (клік → емісія), інакше не рендерити.
  `DataPage` навігацію **не** виконує (router-agnostic) — лише сигналізує вибір.
- [x] 1.3 Тулбар (`#toolbar`), смуга закладок і банер помилки — **над**
  `.page__body` (не скроляться з тілом), щоб зберегти поточну поведінку
  Tabs/`pipe`/chips. Порядок: заголовок → закладки → тулбар → банер → тіло.

## 2. Рефактор дані-екранів на `DataPage`

- [x] 2.1 `ProjectsView.vue` → `DataPage` (`#actions` = кнопка синку; **закладки**
  через `:tabs`/`v-model:active-tab` = TimeCamp/Jira → `router.push`; тіло =
  `<router-view>`); прибрати локальні `.page`/`PageHeader`/`Tabs`/`data-error` —
  показовий приклад використання закладок каркаса.
- [x] 2.2 `TimeCampView.vue` → `DataPage` (без actions/toolbar; тіло =
  `DataTable`).
- [x] 2.3 `JiraView.vue` → `DataPage` (без actions/toolbar; тіло = `DataTable`).
- [x] 2.4 `TempoView.vue` → `DataPage` (`#actions` = «Синхронізувати вибрані»;
  `#toolbar` = `.pipe`-бар; тіло = `DataTable`).
- [x] 2.5 `JournalView.vue` → `DataPage` (`#actions` = наявні дії; `#toolbar` =
  `.cal__chips`-фільтри; тіло = `DataTable`).
- [x] 2.6 `UsersView.vue` → `DataPage` (`#actions` = «Додати користувача»; тіло
  = `DataTable` + `Sheet`-форма лишається).

## 3. Прибирання `PageHeader`

- [x] 3.1 Grep по `PageHeader` — переконатися, що єдині споживачі переведені;
  видалити `components/data/PageHeader.vue` (або лишити як приватний під-компонент
  `DataPage`, якщо так чистіше). `CalendarView` — не чіпати.

## 4. Перевірка

- [x] 4.1 `npm run build` (`vue-tsc --noEmit` + `vite build`) — чисто.
- [ ] 4.2 Браузерний QA (наживо): усі 6 екранів виглядають і поводяться як до
  рефактора (заголовок, дії у правому куті, тулбар/фільтри, банер помилки, тіло
  зі скролом); без візуальних/функційних регресій.

## 5. Memory Bank

- [x] 5.1 Після реалізації — оновити `activeContext.md`/`progress.md` (статус
  зміни) і, за потреби, `systemPatterns.md` (новий каркас `DataPage` як
  стандарт для дані-екранів) через скіл `memory-bank-manager`.
