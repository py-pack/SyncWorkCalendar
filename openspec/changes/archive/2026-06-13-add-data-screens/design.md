## Context

Фаза 3 переносу дизайну Sync Work — решта екранів поверх уже наявного REST API
(`add-rest-api`) і фундаменту (`add-web-ui-foundation`). Більшість екранів
переюзають готові endpoint-и; новий бекенд потрібен лише для Users CRUD
(рішення користувача) і мінімального читання Jira-задач (модель `JRIssue` є,
endpoint-а немає). RBAC і untracked-matching — свідомо відкладені.

**Джерело дизайну (локально):** `docs/design/`. Релевантні
`docs/design/project/src/tables.jsx` (TimeCamp/Jira/Tempo + табличний каркас),
`journal.jsx` (журнал `api_jobs` + verify), `users.jsx` (екран користувачів +
форма) і `tables.css`. Завантажений OpenAPI наявного API —
`docs/design/project/uploads/sync.work.json`.

Наявні факти бекенду: `tc_projects` має `PATCH` (is_sync, issue_key);
`jr_projects` має `is_watched`/`is_archved`, але лише `GET`; `JRIssue` —
модель є, endpoint немає; `worklog_sync_tasks` і `api_jobs` повністю покриті
read/verify/sync-тригерами; `api_users` має `username` (унікальний,
`NOT NULL` — **використаємо як відображуване ім'я**, окрему колонку `name`
не додаємо, рішення користувача), `password_hash` (`NOT NULL` — **зробимо
nullable**), `worker_key/is_active` (+ `email` із фази 1).

## Goals / Non-Goals

**Goals:**

- Три табличні екрани (TimeCamp/Jira/Tempo), журнал, користувачі — 1:1 за
  візуалом прототипу.
- Users CRUD з invite-флоу без пароля (вхід через Google за e-mail).
- Мінімальний Jira-read (`GET /jr-issues`, `PATCH /jr-projects/{id}`).

**Non-Goals:**

- RBAC-ролі (енфорс) — окрема зміна `add-rbac`.
- Untracked → issue matching — окрема зміна `add-untracked-matching`.
- Зміна наявних контрактів api-jobs / sync-status / sync-triggers.

## Decisions

### D1 — Users invite без пароля; вхід через Google за e-mail

Форма дизайну не має поля пароля — лише ім'я/e-mail/worker_key/роль. Тож
`POST /users` створює користувача **без пароля** (`password_hash = NULL`), а
вхід відбувається через Google за `email` (узгоджено з `api-google-auth` із
фази 1). Це робить `password_hash` nullable. Поле «ім'я» з форми мапиться на
наявний `username` (рішення користувача — окрему колонку `name` не додаємо),
тож єдина зміна схеми — `password_hash → nullable`. Логін/пароль для такого
користувача неможливий (повертає `401`), що коректно.

- **Чому так:** цілісний UX «адмін запрошує → користувач входить Google»;
  не змушуємо вигадувати/розсилати тимчасові паролі.
- **Чому `username`, а не нова колонка `name`:** `username` уже є
  (`NOT NULL`, `UNIQUE`) і нічим не зайнятий для invite-користувачів (вони не
  входять логіном/паролем) — переюз прибирає колонку й половину міграції.
  Наслідок: відображуване ім'я **унікальне** (дубль → `409`, як і для e-mail).
- **Альтернатива:** генерувати тимчасовий пароль і слати лист (відкинули —
  немає поштового тракту; Google-вхід уже є). Опційно лишаємо можливість
  задати пароль пізніше.

### D2 — RBAC відкладено, але не блокує Users CRUD

Селектор ролі у формі лишаємо для повноти UI, але роль **не персиститься і не
енфорситься**. Колонку `role` не додаємо в цій зміні. `/users`-endpoint-и
доступні будь-якому авторизованому (single-user адмін-контекст). Коли прийде
`add-rbac` — додасться колонка `role`, енфорс і обмеження «лише admin».

- **Чому:** користувач явно відклав RBAC; додавати колонку без енфорсу —
  напівзахід, який доведеться міняти.

### D3 — Jira-read: окремий мінімальний endpoint, без write у Jira

`GET /jr-issues` читає вже збережені `jr_issues` (наповнюються наявним
`UpdateJiraTask`); фільтр за проектом. `PATCH /jr-projects/{id}` міняє лише
локальний `is_watched` (як `tc-projects` PATCH міняє локальні прапори). У Jira
нічого не пишемо — лише локальні прапори і читання.

### D4 — «Синхронізувати вибрані» (Tempo) через наявні тригери

Наявний `push-to-tempo` працює period/worker-based. У v1 «синхронізувати
вибрані» мапиться на запуск наявних sync-тригерів для відповідного періоду;
точкова вибірка конкретних `id` (якщо знадобиться) — невелике розширення
тригера, винесене в Open Questions. Кроки конвеєра
(`prepare/resolve/push`) — прямі виклики наявних endpoint-ів.

- **Альтернатива:** одразу додати `ids[]` у push-тригер (можливо, але це
  розширення `api-sync-triggers` — лишаємо за рамками, якщо не критично).

### D5 — Frontend: per-screen stores, переюз каркасу

`stores/tables.ts` (TC/Jira/Tempo), `stores/journal.ts`, `stores/users.ts`.
Спільний `DataTable`/`Tabs`/`StatusBadge`/`SyncBtn` з `frontend-data-tables`.
Кнопки синку показують `idle → running → done`. Журнал і Tempo оновлюють
рядки локально після дій (verify, push), без повного перезавантаження.

## Risks / Trade-offs

- **[`password_hash` стає nullable]** → Mitigation: явна перевірка в логіні
  («немає пароля» → `401`), щоб null не давав обхід автентифікації.
- **[Users CRUD без RBAC доступний усім]** → Mitigation: внутрішній
  single-user інструмент; обмеження «лише admin» прийде з `add-rbac`;
  endpoint-и під токеном.
- **[«Синхронізувати вибрані» мапиться на період, не на id]** → Mitigation:
  чітко документуємо поведінку; за потреби — розширення тригера.
- **[Дубль e-mail між Google-вхід і Users CRUD]** → Mitigation: `email`
  `UNIQUE` (з фази 1), `POST /users` дає `409` на дублікат.

## Migration Plan

1. Backend: `api_users.password_hash` → nullable (колонку `name` не додаємо —
   переюзаємо `username`); alembic → `upgrade head`; оновити `schema.md`.
2. Backend: `users.py` (CRUD), `jr_issues.py` (`GET`), `PATCH /jr-projects/{id}`;
   DAO-методи; схеми.
3. Frontend: каркас таблиць + 5 екранів + stores + методи клієнта.
4. Ручний QA: TC тогли/синк; Jira задачі/тогл; Tempo конвеєр/масовий синк;
   журнал фільтри/деталі/verify; Users create/disable/delete + Google-вхід
   запрошеного.

Rollback: прибрати нові роутери/екрани; колонки `name`/nullable
`password_hash` безпечні (лишаються).

## Resolved Questions

Рішення користувача (2026-06-13) — пріоритет на реалізацію/візуалізацію,
розширення відкладено:

- **`push-to-tempo` з `ids[]`** → відкладено. v1 лишається period-based
  (див. D4); точковий синк вибраних — майбутнє розширення тригера.
- **`last_seen`** → відкладено до окремої зміни. Трекінг останнього входу не
  додаємо; у таблиці користувачів показуємо «—».
- **`name` у `POST /users`** → колонку `name` **не додаємо**; переюзаємо
  наявний `username` як відображуване ім'я (див. D1). Єдина зміна схеми —
  `password_hash → nullable`.
