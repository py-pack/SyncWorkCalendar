## 1. Backend — читання тижня (`GET /calendar`)

- [x] 1.1 Read-метод вибірки блоків тижня за `worker_key` + період:
  `tc_entries` (час, опис, `meta.task`) ⋈ `tc_projects` (`color`/`name`/
  `issue_key`) ⋈ `worklog_sync_tasks` (`status`, `target_id`) у
  `TCEntriesDAO`/`WorklogSyncTaskDAO`. **Без міграції, без мутацій.**
- [x] 1.2 `app/api/schemas/calendar.py`: `CalendarBlock`
  (`id`, `start`, `end`, `issue_key`, `description`, `status`,
  `project{key,name,color}`), `CalendarResponse`
- [x] 1.3 Деривація стану `service`/`tempo`/`synced` із `StatusTaskEnum` (D2);
  `failed` бекенд **не** повертає (його немає у `StatusTaskEnum`, D-015)
- [x] 1.4 `app/api/routers/calendar.py`: `GET /calendar` (період → блоки лише
  поточного `worker_key`), захищений токеном; без токена → `401`

## 2. Frontend — store і клієнт (read-only)

- [x] 2.1 Метод `api/client.ts`: `getCalendar(period)`; типи у `api/types.ts`
- [x] 2.2 `stores/calendar.ts`: блоки тижня, період, фільтри (проект/статус),
  варіант, тижневий тотал, завантаження тижня — **без мутацій блоків**

## 3. Frontend — сітка і блоки

- [x] 3.1 `components/calendar/CalendarGrid.vue`: гутер годин, 7 колонок,
  лінії, смуга робочих годин (Tweaks), лінія «зараз», сьогодні/вихідні
- [x] 3.2 `components/calendar/CalendarBlock.vue`: позиція за `start`/`end`,
  колір проекту, lane-розкладка, 3 варіанти, іконка+бордюр стану
  (`service`/`tempo`/`synced`) + error-стиль `failed` (forward-compat),
  стиснутий вигляд
- [x] 3.3 Денні тоталі в шапках колонок

## 4. Frontend — тулбар і фільтри

- [x] 4.1 `components/calendar/CalendarToolbar.vue`: навігація тижнями,
  діапазон+тиждень, тижневий тотал (білабл-тотал — заглушка, поки `billable`
  не персиститься), перемикач варіанта, кнопка фільтрів. **Кнопка
  «Синхронізувати» — відкладено** (фаза редагування/sync)
- [x] 4.2 `components/calendar/CalendarFilters.vue`: чипи проектів (з кольором)
  і статусів; ховають блоки і впливають на тоталі

## 5. Frontend — панель деталей (перегляд)

- [x] 5.1 `components/calendar/BlockPopover.vue`: **перегляд** проекту/часу/
  `issue`/опису/статусу; закриття по `Escape`/кліку поза. Редагування полів,
  sync і видалення — показані вимкненими (відкладено в майбутні зміни)

## 6. Документація

- [x] 6.1 `api-reference.md`: розділ календаря (`GET /calendar` — read)

## 7. Ручний QA

- [x] 7.1 `GET /calendar` повертає тиждень зі станами і кольорами проектів;
  порожній період → `[]`
- [x] 7.2 Сітка/блоки/3 варіанти/стани рендеряться; lane-розкладка перекриттів
- [x] 7.3 Навігація тижнями; фільтри проект/статус; тоталі перераховуються
- [x] 7.4 Панель деталей відкривається/закривається по `Escape`/кліку поза;
  показує дані блоку

## Поза скоупом (майбутні зміни — `design.md` → Deferred / Future work)

- [ ] `add-calendar-editing`: колонка `billable` + CRUD блоків (create/edit/
  delete/split/duplicate) + drag/resize + per-block і масовий sync через
  наявний `resolve-issues`+`push-to-tempo`
- [ ] `add-worklog-update-flow`: round-trip update/delete вже-`synced` у Tempo
  (активація reserved `pre_update→update→updated`), семантика дубль-`synced`
- [ ] Явний `project_key`/FK у WST для надійного кольору (Q4)
