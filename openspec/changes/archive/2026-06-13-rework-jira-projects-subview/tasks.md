## 1. Frontend — стор `tables.ts`

- [x] 1.1 Додати фільтр-стан `jrActive` (`'active' | 'inactive' | 'all'`, дефолт
  `all`) — клієнтський фільтр Jira-під-вʼюхи за `is_watched` (як `tcActive`).
- [x] 1.2 Замінити `toggleJrWatched(p)` на `saveJrWatched(id, is_watched)`
  (`PATCH /jr-projects/{id} {is_watched}` + локальне оновлення рядка) для попапу;
  оновити експорт.

## 2. Frontend — попап налаштувань синку Jira

- [x] 2.1 Створити `components/projects/JrSyncSettingsModal.vue` на `Sheet`-
  патерні (як TimeCamp `SyncSettingsModal`, але **лише тогл** «увімкнути/вимкнути
  синхронізацію» `is_watched`; **без** select-а задачі; **Save завжди дозволено**).
- [x] 2.2 На Save → `store.saveJrWatched(project.id, enabled)`; закрити модалку,
  оновити рядок.

## 3. Frontend — під-вʼюха Jira (`JrProjects.vue`)

- [x] 3.1 Прибрати інлайн-`Toggle` `is_watched`; рядок показує `key`/`name`/
  `issues_count`, **індикатор стану синку** («відстежується / ні» за `is_watched`)
  і кнопку-шестерню; `@dblclick` по рядку теж відкриває попап.
- [x] 3.2 Архівні проекти (`is_archived`) — сірі/напівпрозорі.
- [x] 3.3 Додати тулбар: контрол **фільтра** `усі | у синку | не в синку`
  (клієнтський, за `is_watched` через `jrActive`) і **швидке поле пошуку** по
  локальних даних (`key`/`name`, case-insensitive); обидва комбінуються.
- [x] 3.4 Підключити `JrSyncSettingsModal` (відкриття шестернею / подвійним
  кліком; `@close`).

## 4. Frontend — i18n

- [x] 4.1 Переюзати наявні ключі (`flt_all`/`flt_active`/`flt_inactive`,
  `sync_state_on`/`sync_state_off`, `search`, `settings`, `blk_save`/`blk_cancel`);
  за потреби додати ключ заголовка/тогла попапу Jira (UK+EN).

## 5. Frontend — перевірка

- [x] 5.1 `npm run build` (`vue-tsc --noEmit` + `vite build`) — чисто.
- [ ] 5.2 Браузерний QA (наживо): `/projects/jira` — фільтр за станом синку,
  пошук по локальних даних, попап (шестерня + подвійний клік) з одним тоглом,
  Save завжди активний, тьмяні архівні, лічильник задач для всіх; інлайн-тогла
  немає.

## 6. Memory Bank

- [x] 6.1 Після реалізації — оновити `activeContext.md`/`progress.md` (статус
  зміни) через скіл `memory-bank-manager`; за потреби — `decisinLog.md`
  (дзеркало TimeCamp-рішень на Jira: фільтр `is_watched`/пошук/попап-тогл).
