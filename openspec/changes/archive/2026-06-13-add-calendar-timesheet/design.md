## Context

Фаза 2 переносу дизайну Sync Work. Фундамент (дизайн-система, shell, auth) дає
`add-web-ui-foundation`; календар замінює заглушку-роут `calendar` реальним
екраном. Скоуп фази свідомо звужено до **візуалізації (read-only)** — календар
показує тиждень, але не редагує блоки і не пише на бекенд (рішення користувача;
усе редагування/sync/round-trip → майбутні зміни, див. **Deferred / Future
work**).

**Джерело дизайну (локально):** `docs/design/`. Для календаря релевантні
`docs/design/project/src/calendar.jsx` (сітка, тулбар), `calendar-block.jsx`
(блок, стани синку, popover деталей) і `calendar.css` (сітка, 3 варіанти
блоків, фільтри). Звірятися поекранно з прототипом (інтеракції редагування з
прототипу — поза цією фазою).

Поточна доменна модель (Memory Bank, звірено з кодом):

- `tc_entries` — таймер-записи TimeCamp (`start_at`/`end_at`/`description`/
  `duration` computed, `meta.task` = розпарсений `issue_key`, `tc_project_id`).
- `tc_projects` — проекти TimeCamp (`name`, `color`, `issue_key`, `is_sync`) —
  **джерело кольору і назви** проекту.
- `worklog_sync_tasks` (WST) — стан-машина синку worklog-а
  (`pre_create → create → created`, поля `issue_key`, `content`, `started_at`,
  `time_spent`, `status`, `source_id` (NOT NULL → `tc_entry`), `target_id`,
  `worker_key`); зарезервовані стани `pre_update/update/updated/sync` **без
  реалізації**. У `StatusTaskEnum` **немає** `failed` (це статус `api_jobs`,
  не WST — D-015).
- TimeCamp-клієнт уміє тільки **читати** — запису назад немає.

Відкрите питання Memory Bank («сценарій оновлення worklog-ів») ця фаза **не
закриває** — воно переходить у майбутню `add-worklog-update-flow`.

## Goals / Non-Goals

**Goals:**

- `GET /calendar` — тиждень блоків зі станом синку для `worker_key`, **read-only**
  поверх наявних таблиць (без міграції).
- Frontend-екран 1:1 за візуалом прототипу: сітка, блоки (3 варіанти), стани
  синку (`service`/`tempo`/`synced`) + error-стиль `failed` (forward-compat),
  тулбар, фільтри, навігація тижнями, тоталі, панель деталей (перегляд).

**Non-Goals (цієї фази; → майбутні зміни):**

- Будь-який запис на бекенд: редагування / створення / split / duplicate /
  delete блоків, per-block і масовий sync.
- Колонка `worklog_sync_tasks.billable` і її персистенс.
- Round-trip у Tempo (update/delete вже-`synced`, активація reserved-станів).
- Запис назад у TimeCamp (джерело лишається read-only назавжди).
- Untracked→issue matching, власний трекер часу, мульти-користувацький перегляд
  чужих календарів.

## Decisions

### D1 — Блок = read-проекція `tc_entry` ⋈ WST (TimeCamp read-only)

Календарний блок для read-шляху деривується з `tc_entry` (відпрацьований час:
`start_at`/`end_at`/`description`/`meta.task`) і збагачується відповідним WST
(join за `WST.source_id = tc_entry.id`) для **стану синку**. Проект (колір/назва)
— з `tc_project` за `tc_entry.tc_project_id` (`color`, `name`, `issue_key`).

WST лишається **майбутньою редаговною одиницею** worklog-а; ця фаза його **не
мутує**. Перехід «блок = редагований WST» з персистенсом — у `add-calendar-editing`.

- **Чому через `tc_entry`, а не лише WST:** read має показати **весь**
  відпрацьований час, зокрема entries, що ще не мають WST (стан `service`).
- **Альтернатива (відкинули на цей етап):** окрема таблиця
  `calendar_blocks`/`time_blocks` — більше коду; має сенс із власним трекером
  (roadmap stage 3). Лишаємо як шлях відступу.

### D2 — `service`/`tempo`/`synced` як проекція станів WST (без `failed` на бекенді)

Стан блоку для UI — проекція `StatusTaskEnum`:

| Блок (UI) | Джерело                                       |
|-----------|-----------------------------------------------|
| `service` | немає WST або WST у `pre_create`              |
| `tempo`   | WST у `create` (готовий до пушу / очікує)     |
| `synced`  | WST у `created` (є `target_id`)              |

Read-шар **не повертає** `failed`: у `StatusTaskEnum` такого статусу немає
(`failed` — це стан `api_jobs`, не worklog-таска; D-015). `failed` лишається
**суто фронтовим візуальним станом** (forward-compat) — компонент блоку вміє
його малювати окремим error-стилем, але в read-only фазі жоден блок не
позначається `failed` бекендом. Реальне джерело `failed` зʼявиться у фазі
sync (коли per-block push зможе впасти).

- **Альтернатива:** віддавати UI сирий `StatusTaskEnum` (відкинули — дизайн
  оперує трьома станами service/tempo/synced + окремий error-візуал).

### D3 — Жодних змін схеми в цій фазі

`GET /calendar` читає **наявні** `tc_entries` / `worklog_sync_tasks` /
`tc_projects`. Колонка `billable` **не додається** — без редагування її нема як
виставити (немає setter-а), а в наявних таблицях джерела `billable` немає. Тому
колонка + міграція відкладені у `add-calendar-editing`. Білабл-тотал у тулбарі —
заглушка (поки `billable` не персиститься, дорівнює тижневому тоталу).

### D4 — Frontend: read-only Pinia-store, геометрія з прототипу

`stores/calendar.ts` тримає блоки тижня, фільтри (проект/статус), обраний
варіант і тоталі — **без мутацій блоків**. Тиждень перезавантажується при
навігації. Зберігаємо геометричні константи прототипу як дефолти розкладки:
робочий діапазон 08:00–21:00, lane-розкладка перекриттів, висота години, лінія
«зараз». Снап / drag / resize — поза цією фазою (потрібні лише для редагування).

## Risks / Trade-offs

- **[Деривація проекту з префікса `issue_key` неоднозначна]** → Mitigation:
  колір беремо з `tc_project.color`; fallback — зіставлення префікса `issue_key`
  із `JRProject.key` / `tc_project.issue_key`; невідомий → нейтральний колір.
  Надійний явний project FK — відкладено (Q4, нижче).
- **[`worker_key`-скоупінг для `service`-блоків]** → `tc_entries` не мають
  `worker_key` (його несе лише WST). У поточному single-user-контексті це
  безпечно; точний мульти-користувацький скоупінг (worker_key на джерелі
  entries) — майбутня робота.
- **[`failed` без бекенд-джерела]** → Mitigation: рендериться лише як
  forward-compat візуал; у read-only фазі бекенд блок `failed` не віддає (D2).

## Migration Plan

1. Backend: read-метод вибірки тижня за `worker_key`+період у
   `WorklogSyncTaskDAO`/`TCEntriesDAO`; `GET /calendar` router + схема. **Без
   alembic.**
2. Frontend: `CalendarView` + компоненти + read-only `stores/calendar.ts` +
   `getCalendar` у клієнті; сітка/блоки/варіанти/стани/тулбар/фільтри/деталі.
3. Ручний QA: read тижня; стани і кольори; 3 варіанти; lane-перекриття;
   навігація тижнями; фільтри; тоталі; панель деталей (перегляд).

Rollback: прибрати `/calendar` і `CalendarView`, повернути заглушку-роут.
Жодних змін БД відкочувати не треба.

## Deferred / Future work

Зафіксовано як майбутні зміни (щоб не загубити). Послідовність орієнтовна.

### `add-calendar-editing` — редагування блоків + sync через наявний pipeline

Найбільший винесений шматок. Що треба зробити:

- **БД:** `worklog_sync_tasks.billable BOOLEAN` (default `TRUE`); опц.
  `is_manual` для ручних/дубльованих блоків. Увага: зараз `WST.source_id` —
  `NOT NULL` (кожен WST вʼязаний до `tc_entry`); для ручних блоків треба зробити
  `source_id` nullable або ввести `is_manual`. Одна alembic-ревізія, оновити
  `docs/technical/database/schema.md`.
- **Backend CRUD/split над WST:**
  - `POST /calendar/blocks` — створити/дублювати блок (`pre_create`, стан
    `service`) → `201`.
  - `PATCH /calendar/blocks/{id}` — `start`/`end` (→ `started_at`/`time_spent`),
    `issue_key`, опис, `billable`, проект; валідація `end>start`; чужий/
    відсутній → `404`.
  - `DELETE /calendar/blocks/{id}` — видалити несинхронізований.
  - `POST /calendar/blocks/{id}/split` — поділ на два суміжні блоки.
  - DAO-методи CRUD/split.
- **Backend sync (наявний pipeline, без нової логіки пушу):**
  `POST /calendar/blocks/{id}/sync` — обгортка над `worklog-tasks/resolve-issues`
  + `push-to-tempo` для одного таска; масовий week-sync — над тими ж тригерами
  для всіх `tempo`-блоків тижня; перевірка `worker_key` (null → `400`); кожен
  рух — у `api_jobs` через `jobs_wrapper` (`needs_verification`).
- **Frontend:** drag&drop (снап 5 хв, межі дня, `PATCH` на `mouseup`, відкат на
  помилці), resize краями, редагування полів у панелі деталей, контекстне меню
  (деталі/sync/змінити задачу/дублювати/розділити/видалити), кнопка
  «Синхронізувати» (масовий sync зі станом виконання), реальний білабл-тотал.

### `add-worklog-update-flow` — round-trip update/delete вже-`synced` у Tempo  [Q1 + Q2]

Найдорожча і найризикованіша частина (пише в зовнішній Tempo) — тому окремо.
Що треба зробити:

- Активувати зарезервовані `pre_update → update → updated` (`StatusTaskEnum`) у
  `WorllogSyncTask`.
- Нові методи сервісу: `Tempo.update_worklog(target_id, ...)`,
  `Tempo.delete_worklog(target_id)` (Tempo API `PUT`/`DELETE /worklogs/{id}`).
- `PATCH`/`DELETE` блоку у стані `synced` → update/delete worklog у Tempo за
  `target_id`; **TimeCamp не чіпати**; кожен рух — у `api_jobs`
  (`needs_verification`, патерн `jobs_wrapper`).
- **Семантика «дублювати вже-`synced`» (Q2):** копія створюється як `service`
  без `target_id` → при подальшому sync стає **новим** worklog. Підтвердити, чи
  взагалі дозволяти дубль уже-`synced`.
- Закриває відкрите питання Memory Bank «сценарій оновлення worklog-ів» і
  оновлює `productContext.md`/`systemPatterns.md` (state-machine з
  `pre_update→update→updated`).

### Явний `project_key`/FK у WST для кольору  [Q4]

Зараз колір проекту деривується з префікса `issue_key` (зіставлення з
`JRProject.key`) / `tc_project.issue_key` / `tc_project.color`. Для надійності
кольору — додати явний `project_key` чи FK у WST. Відкладено; розглянути разом
із `add-calendar-editing`.
