## 1. Навігація та маршрути (каркас)

- [x] 1.1 Розширити `NavItem` у `front/src/lib/nav.ts` опційними полями `path`
  (явний шлях, якщо ≠ `/${name}`) і `children` (під-пункти)
- [x] 1.2 Додати у секцію «Дані» `NAV` **єдиний пункт `projects`** (першим,
  → `/projects`, `nav_projects`) із `children` `projects-timecamp`
  (`/projects/timecamp`) та `projects-jira` (`/projects/jira`); під-вʼюхи —
  таби всередині екрана, окремих пунктів навігації немає. `AppShell` рендерить
  пункт одним лінком, активність — за `route.matched`
- [x] 1.3 Перейменувати пункти секції «Дані»: `timecamp` → «TimeCamp · Записи»,
  `jira` → «Jira · Задачі» (через нові i18n-ключі, маршрути `/timecamp`,
  `/jira` без змін)
- [x] 1.4 Оновити `SCREENS`/`validScreen`, щоб коректно нормалізувати відомі
  шляхи (включно з вкладеними `projects/*`) для відновлення `ui.route`
- [x] 1.5 У `front/src/router/index.ts` додати батьківський маршрут `/projects`
  з `redirect` на `/projects/timecamp` і дочірніми `timecamp`/`jira`
  (`ProjectsView` + під-вʼюхи); решта екранів — без змін

## 2. Екран «Проекти»

- [x] 2.1 Створити `front/src/views/ProjectsView.vue` — контейнер із
  `PageHeader` і перемикачем під-вʼюх (`Tabs`), привʼязаним до маршруту
  (`/projects/timecamp` ↔ `/projects/jira`), із `<router-view>` для дочірніх
- [x] 2.2 Створити `front/src/views/projects/TcProjects.vue` — перенести
  таблицю TC-проектів із `TimeCampView` (колонки `name`/`issue_key`/
  `entries_count`/`is_sync`, тогл `is_sync` → `store.toggleTcSync`)
- [x] 2.3 Створити `front/src/views/projects/JrProjects.vue` — перенести
  таблицю Jira-проектів із `JiraView` (колонки `key`/`name`/`issues_count`/
  `is_watched`, тогл `is_watched` → `store.toggleJrWatched`)
- [x] 2.4 Реалізувати авто-синк проектів на екрані «Проекти»
  (`POST /sync/timecamp/projects` + `POST /sync/jira/projects`) із вікном
  свіжості; за потреби виділити гранулярні методи стора (`autoSyncTcProjects`/
  `autoSyncJrProjects`)

## 3. Спрощення екранів TimeCamp і Jira

- [x] 3.1 У `front/src/views/TimeCampView.vue` прибрати вкладки і таблицю
  проектів — лишити лише незіставлені записи (`store.tcUntracked`), без
  `Tabs`; авто-синк звузити до записів (`POST /sync/timecamp/entries`)
- [x] 3.2 У `front/src/views/JiraView.vue` прибрати вкладки і таблицю проектів
  — лишити лише задачі (`store.jrIssues`), без `Tabs`; авто-синк звузити до
  задач (re-sync відомих ключів)
- [x] 3.3 Перевірити, що `stores/tables.ts` лишається сумісним (ті самі поля
  `tcProjects`/`tcUntracked`/`jrProjects`/`jrIssues`); правити лише методи
  авто-синку за потреби з кроків 2.4/3.1/3.2

## 4. i18n та підписи

- [x] 4.1 Додати в `front/src/i18n/strings.ts` (UK+EN) ключі: секція
  `nav_section_projects`; пункти «Проектів» (`nav_projects_timecamp`,
  `nav_projects_jira`); перейменовані `nav_timecamp` → «TimeCamp · Записи» /
  «TimeCamp · Entries», `nav_jira` → «Jira · Задачі» / «Jira · Issues»
- [x] 4.2 Додати заголовки екрана «Проекти» (`pr_title`, `pr_desc`) і оновити
  `tc_title`/`tc_desc` (під записи) та `jr_title`/`jr_desc` (під задачі) в обох
  мовах
- [x] 4.3 Перевірити `StringKey`-типізацію (нові ключі присутні в обох мовних
  словниках, `vue-tsc` не падає)

## 5. Перевірка

- [x] 5.1 `npm run build` (`vue-tsc --noEmit` + `vite build`) — без помилок
- [ ] 5.2 Ручний QA навігації: секція «Проекти» активна на `/projects/*`,
  секція «Дані» активна на `/timecamp`/`/jira`; згорнута навігація показує
  іконки/`title`
- [ ] 5.3 Ручний QA маршрутів: `/projects` → редірект `/projects/timecamp`;
  перемикач під-вʼюх змінює URL; back/forward і перезавантаження відновлюють
  саме `/projects/jira`
- [ ] 5.4 Ручний QA даних: тогли `is_sync`/`is_watched` персистяться
  (`PATCH /tc-projects/{id}`, `PATCH /jr-projects/{id}`); `/timecamp` показує
  незіставлені записи; `/jira` показує задачі; авто-синк кожного джерела
  спрацьовує рівно з одного екрана
- [x] 5.5 `openspec validate extract-projects-screen --strict` — без помилок
