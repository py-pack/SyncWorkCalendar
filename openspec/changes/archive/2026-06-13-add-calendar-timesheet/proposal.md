## Why

Календар — **головний екран** дизайну Sync Work і центральний робочий
інструмент: тижневий timesheet, де видно відпрацьований час блоками за
проектами і стан кожного блоку відносно синку (`тільки TimeCamp` / `в Tempo` /
`синхронізовано`). Сьогодні візуального тижневого подання немає взагалі — час
видно лише опосередковано через таблиці й sync-таски.

Це **фаза 2 із трьох** (після `add-web-ui-foundation`). Скоуп цієї фази свідомо
звужено до **візуалізації (read-only)**: календар **показує** тиждень, але ще
**не редагує** блоки і **не пише** на бекенд. Усе редагування, створення,
sync і round-trip у Tempo винесено в окремі майбутні зміни (див.
`design.md` → **Deferred / Future work**). Так ми отримуємо цілісний,
придатний до релізу екран-перегляд, а найскладнішу частину (запис у Tempo)
робимо окремо й без ризику для read-шляху.

## What Changes

- **Backend — читання тижня:** `GET /calendar` повертає блоки робочого часу
  для авторизованого `worker_key` за період (тиждень): час, проект (для
  кольору), `issue_key`, опис і **стан синку** (`service` / `tempo` /
  `synced`), зведений із `tc_entries` ↔ `worklog_sync_tasks`. **Лише читання
  наявних таблиць** — без нових колонок і без alembic-міграції.
- **Frontend — екран календаря:** тижнева сітка (Пн–Нд, гутер годин, лінії),
  блоки за проектами з lane-розкладкою для перекриттів, **3 варіанти** блоків
  (`basic`/`soft`/`bold`), іконка+бордюр стану синку, окремий error-стиль для
  `failed`-блоків (forward-compat), смуга робочих годин, лінія «зараз»,
  виділення сьогодні/вихідних (за Tweaks).
- **Frontend — тулбар і фільтри:** навігація тижнями (prev/today/next),
  діапазон і номер тижня, тижневий тотал, перемикач варіанта, фільтри за
  проектами і статусом.
- **Frontend — перегляд деталей:** клік по блоку відкриває панель деталей
  **тільки для перегляду** (проект, час, `issue`, опис, статус). Редагування
  полів, sync і видалення — поза скоупом цієї фази (показані вимкненими /
  відкладені).

## Capabilities

### New Capabilities

- `frontend-calendar`: тижневий timesheet-екран (**read-only**) — сітка, блоки
  (3 варіанти), стани синку (+ error-стиль), тулбар, фільтри, навігація
  тижнями, тоталі, панель деталей (перегляд).
- `api-calendar`: backend для **читання** календаря — тиждень блоків (entries ↔
  worklog-sync-tasks) зі станом синку. Лише читання, без мутацій.

### Modified Capabilities

<!-- Жодна наявна capability-вимога не змінюється: api-calendar додає один
     read-endpoint, не переписуючи контракти api-sync-status/api-sync-triggers. -->

## Impact

- **Новий код (frontend):** `front/src/views/CalendarView.vue`,
  `components/calendar/*` (`CalendarGrid`, `CalendarBlock`, `BlockPopover`,
  `CalendarToolbar`, `CalendarFilters`), `stores/calendar.ts` (**read-only**),
  метод `getCalendar` у `api/client.ts` + типи.
- **Новий код (backend):** `app/api/routers/calendar.py` (`GET /calendar`),
  `app/api/schemas/calendar.py`, read-метод вибірки тижня у
  `WorklogSyncTaskDAO`/`TCEntriesDAO`.
- **БД:** **без змін** — read-only поверх наявних `tc_entries` /
  `worklog_sync_tasks` / `tc_projects`. **Без alembic-ревізії.**
- **Залежності:** без нових.
- **Документація:** `api-reference.md` (розділ календаря — read).
- **Поза скоупом (майбутні зміни — `design.md` → Deferred):** редагування /
  створення / split / duplicate / delete блоків, колонка `billable`, per-block
  і масовий sync, update/delete вже-`synced` worklog-ів у Tempo (reserved
  states), явний project FK для кольору. Заглушка-роут `calendar` з фази 1
  замінюється реальним **read-only** екраном.
- **Ризики:** мінімальні — лише читання наявних даних; найскладніша частина
  (запис у Tempo) винесена в окремі зміни.
