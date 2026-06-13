## 1. Backend — спільний хелпер «активності» задачі

- [x] 1.1 Додати хелпер `is_issue_active(status: str | None) -> bool` (напр. у
  `app/api/schemas/jr_issues.py` або `app/core/utils/`) з константним «done»-сетом
  (EN+UK: `done`/`closed`/`resolved`/`cancelled`/`won't do`/`готово`/`закрито`/
  `виконано`/`скасовано`/`вирішено`), case-insensitive + trim. `None` → `True`.

## 2. Backend — `GET /tc-projects` (дерево + маппінг + фільтр)

- [x] 2.1 У `schemas/tc_projects.py`: прибрати `TCProjectWithCount.entries_count`;
  у `TCProjectResponse` (або новій read-схемі) додати `parent_id: int | None`,
  `color: str | None`, `issue_name: str | None`, `issue_active: bool | None`.
- [x] 2.2 У `routers/tc_projects.py`: прибрати параметри `start`/`end` і
  `_default_period`/`entries_count`-subquery; додати `Query` `active:
  Literal["active","inactive","all"] = "all"`.
- [x] 2.3 Реалізувати вибірку: `SELECT tc_projects LEFT JOIN jr_issues ON
  tc_projects.issue_key = jr_issues.key`, віддавати `issue_name`/(статус→
  `issue_active` через хелпер 1.1); фільтр за `is_archived` згідно `active`;
  сортування за `name`.
- [x] 2.4 Невалідне значення `active` → `422` (через `Literal`/валідатор); без
  токена → `401` (наявна залежність `get_current_user`).

## 3. Backend — `GET /jr-issues` (пошук + limit + active)

- [x] 3.1 У `dao/jr_issues_dao.py` `list_filtered`: додати параметри `q: str |
  None` (ILIKE `%q%` по `key` OR `name`) і `limit: int | None`; при `q` —
  `ORDER BY updated_at DESC`; застосувати `limit` (капнути ≤50).
- [x] 3.2 У `schemas/jr_issues.py` `JRIssueItem`: додати похідне `active: bool`
  (через хелпер 1.1; `status` лишається).
- [x] 3.3 У `routers/jr_issues.py`: додати `Query` `q` і `limit` (дефолт 10),
  пробросити в DAO; мапити `active` у відповідь.

## 4. Backend — перевірка

- [x] 4.1 `uv run uvicorn app.api.app:app` піднімається; ручний smoke:
  `GET /tc-projects` (поля присутні, без `entries_count`/period),
  `GET /tc-projects?active=inactive`, `GET /jr-issues?q=...&limit=10`
  (≤10, `active` присутній), `401` без токена.

## 5. Frontend — типи й клієнт API

- [x] 5.1 У `api/types.ts`: `TCProject` — прибрати `entries_count`, додати
  `parent_id: number | null`, `color: string | null`, `issue_name: string |
  null`, `issue_active: boolean | null`; `JRIssue` — додати `active: boolean`.
- [x] 5.2 У `api/client.ts`: `tcProjects(active?)` — прибрати `period`, додати
  `?active=`; `jrIssues({ projectId?, q?, limit? })` — додати `q`/`limit`.

## 6. Frontend — стор `tables.ts`

- [x] 6.1 Прибрати `autoSyncProjects` і period-залежність; **розділити** loader
  по під-вʼюхах: `loadTcProjects(active)` (лише `GET /tc-projects`, з фільтром у
  стані) і `loadJrProjects()` (лише `GET /jr-projects`). Кожен **ідемпотентний**
  (guard «вже завантажено», щоб перемикання вкладок не пере-запитувало).
- [x] 6.2 Додати `syncProjects()` (POST tc+jr projects → reload **поточної**
  під-вʼюхи) для явної кнопки; додати `jrIssueSearch(q)`
  (→ `api.jrIssues({ q, limit: 10 })`).
- [x] 6.3 `toggleTcSync` замінити на `saveTcSync(id, { is_sync, issue_key? })`
  (PATCH + локальне оновлення рядка), що використовує попап.

## 7. Frontend — хелпер дерева

- [x] 7.1 Створити `lib/tree.ts`: `buildTree(items)` → корені + `children[]`,
  orphan-hoisting (вузол з відсутнім/відфільтрованим `parent_id` — у корінь),
  стабільне сортування за `name`; + хелпер валідації hex-кольору
  (`^#?[0-9a-fA-F]{3,8}$`) з нейтральним фолбеком.

## 8. Frontend — під-вʼюха TimeCamp (дерево, тег, фільтр)

- [x] 8.1 Переписати `views/projects/TcProjects.vue`: на `onMounted` →
  `loadTcProjects(active)` (власний запит вкладки); рекурсивний рендер дерева з
  відступом за глибиною; акцент кольором; архівні вузли — сірі/напівпрозорі.
- [x] 8.2 Прибрати інлайн-`Toggle` `is_sync`; додати індикатор стану синку,
  кольоровий тег задачі **одразу біля назви** (`issue_key` + `issue_name`, тінт
  `color`, тьмяний при `issue_active=false`) і кнопку-шестерню; `@dblclick` теж
  відкриває попап.
- [x] 8.3 Додати контрол фільтра **за станом синку** `усі | у синку | не в синку`
  (клієнтський, за `is_sync`, без re-fetch) і **швидке поле пошуку** по локальних
  даних (`name`/`issue_key`/`issue_name`, case-insensitive, клієнтський).
- [x] 8.4 У `views/projects/JrProjects.vue`: на `onMounted` → `loadJrProjects()`
  (Jira-проекти тягнуться лише при відкритті цієї вкладки; ідемпотентно).

## 9. Frontend — попап налаштувань синку

- [x] 9.1 Створити модалку (напр. `components/projects/SyncSettingsModal.vue`):
  тогл «увімкнути синк» + select задачі з пошуком (debounce → `jrIssueSearch`,
  до 10, закриті тьмяні); показ назви вже-змапованої задачі з `issue_name`.
- [x] 9.2 Правило Save: disabled, коли синк увімкнено й задачу не обрано;
  вимкнений синк → Save дозволено, `issue_key` зберігається.
- [x] 9.3 На Save → `saveTcSync(...)` (PATCH), закрити модалку, оновити вузол.

## 10. Frontend — шапка й видалення авто-синку

- [x] 10.1 У `views/ProjectsView.vue`: **прибрати** завантаження даних з
  `onMounted` (кожна під-вʼюха вантажить себе сама; прибрати `autoSyncProjects`);
  лічильники вкладок зробити лінивими (badge лише для завантаженого джерела);
  додати в `PageHeader` кнопку «Синхронізувати проекти» → `store.syncProjects()`
  (синк **кожного сервісу незалежно** — TimeCamp + Jira через `allSettled`).
- [x] 10.2 У `i18n/strings.ts` (UK+EN): ключі фільтра, стану синку, заголовка/
  лейблів попапу, плейсхолдера пошуку, кнопки синку, тексту тега.

## 11. Frontend — перевірка

- [x] 11.1 `npm run build` (`vue-tsc --noEmit` + `vite build`) — чисто.
- [ ] 11.2 Браузерний QA: відкриття `/projects/timecamp` робить **лише 1** запит
  (`GET /tc-projects`, без `GET /jr-projects` і без POST-синку); дерево/кольори/
  архівні-тьмяні; тег задачі з назвою; попап (шестерня + подвійний клік),
  правило Save; кнопка явного синку працює; фільтр активні/неактивні/всі; Jira-
  проекти тягнуться лише при переході на вкладку Jira.

## 12. Memory Bank

- [x] 12.1 Після реалізації — оновити `activeContext.md`/`progress.md` (статус
  зміни) і `decisinLog.md` (нове рішення: BREAKING-контракт `/tc-projects`,
  прибраний авто-синк, дерево/попап) через скіл `memory-bank-manager`.
