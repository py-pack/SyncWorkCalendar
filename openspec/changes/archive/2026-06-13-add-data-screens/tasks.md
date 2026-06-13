## 1. Backend — міграція `api_users`

- [x] 1.1 Зробити `password_hash` nullable у моделі `api_user.py` (колонку
  `name` НЕ додаємо — відображуване ім'я = наявний `username`)
- [x] 1.2 `alembic revision --autogenerate -m "make_password_hash_nullable_api_users"`,
  перевірити, `alembic upgrade head`
- [x] 1.3 Оновити `docs/technical/database/schema.md`

## 2. Backend — Users CRUD (`api-users-management`)

- [x] 2.1 `app/api/schemas/users.py`: `UserItem` (без `password_hash`,
  поле `username`), `UserCreate` (`username`, `email`, `worker_key`, опц.
  `password`), `UserPatch` (`username`/`worker_key`/`is_active`)
- [x] 2.2 `APIUserDAO`: `list_all`, `create`, `update`, `delete`,
  перевірка унікальності `email` (регістронезалежно) і `username`
- [x] 2.3 `app/api/routers/users.py`: `GET /users`, `POST /users`
  (invite без пароля → `password_hash NULL`; дубль email/username → `409`),
  `PATCH /users/{id}` (дубль username → `409`), `DELETE /users/{id}`
- [x] 2.4 Логін: користувач без `password_hash` → `401` (немає чим
  автентифікуватись паролем)
- [x] 2.5 Підключити роутер у `app.py`; доступ під токеном (без RBAC)

## 3. Backend — Jira read (`api-jira-read`)

- [x] 3.1 `JRIssuesDAO.list_filtered(project=None)`
- [x] 3.2 `app/api/schemas/jr_issues.py`: `JRIssueItem`
- [x] 3.3 `app/api/routers/jr_issues.py`: `GET /jr-issues` (фільтр за проектом)
- [x] 3.4 `PATCH /jr-projects/{id}` у `jr_projects.py` (тогл `is_watched`;
  лише локальний прапор; `404` на відсутній)

## 4. Frontend — табличний каркас

- [x] 4.1 `components/data/DataTable.vue` (колонки з рендером, вирівнювання,
  вибір рядків, порожній стан), `Tabs.vue`, `PageHeader.vue`
- [x] 4.2 `components/data/StatusBadge.vue` (мапа статусів) і `SyncBtn.vue`
  (`idle → running → done`)
- [x] 4.3 Методи `api/client.ts` + типи для tc/jr/tempo/jobs/users

## 5. Frontend — екрани TimeCamp / Jira / Tempo

- [x] 5.1 `views/TimeCampView.vue`: вкладки «Проекти» (тогл `is_sync`,
  маппінг, синк) і «Незіставлені» (кнопка «Зіставити» вимкнена)
- [x] 5.2 `views/JiraView.vue`: вкладки «Проекти» (тогл `is_watched`) і
  «Задачі» (`GET /jr-issues`, кольоровий тег проекту, статус)
- [x] 5.3 `views/TempoView.vue`: зведення по статусах, вибір рядків, масовий
  синк вибраних, кнопки конвеєра `prepare/resolve/push`
- [x] 5.4 `stores/tables.ts`: стан трьох екранів, виклики синку зі станами

## 6. Frontend — Журнал синку

- [x] 6.1 `views/JournalView.vue`: таблиця `api_jobs`, фільтри за статусом,
  бейдж `running` зі спінером
- [x] 6.2 Бічна панель деталей (`Sheet`): payload/result/error (JSON),
  виділення помилки
- [x] 6.3 Кнопка «Підтвердити» (рядок + деталі) → `POST /api-jobs/{id}/verify`,
  локальне оновлення статусу
- [x] 6.4 Лічильник `needs_verification` у бейджі навігації

## 7. Frontend — Користувачі

- [x] 7.1 `views/UsersView.vue`: таблиця (аватар, e-mail, `worker_key`,
  тогл активності, меню рядка), нотатка про відсутність реєстрації
- [x] 7.2 Бічна форма «Запросити» (ім'я/e-mail/worker_key, селектор ролі —
  вимкнений/відкладений), без поля пароля → `POST /users`
- [x] 7.3 Деактивація (`PATCH`) і видалення (`DELETE`); `stores/users.ts`

## 8. Документація і Memory Bank

- [x] 8.1 `api-reference.md`: Users CRUD і `jr-issues`/`jr-projects PATCH`
- [x] 8.2 `decisinLog.md`: invite-без-пароля через Google; RBAC/matching
  відкладено окремими змінами (D-015)
- [x] 8.3 `progress.md` / `activeContext.md`: фаза 3; частково закрито
  `add-user-management-cli` (тепер є API)

## 9. Ручний QA

> **Статус (2026-06-13):** частково пройдено живцем у браузері під час сесії —
> підтверджено завантаження даних, тогли `is_sync`/`is_watched` (`PATCH` 200),
> синк-тригери (`POST /sync/...` 200), backend-smoke 16/16 (Users CRUD, дубль
> email/username → 409, passwordless login → 401). Решта сценаріїв (Google-вхід
> запрошеного, verify в UI) **відкладено** — зміну архівовано за рішенням
> користувача без повного проходу секції.

- [ ] 9.1 TimeCamp: тогл `is_sync`/маппінг персистяться; синк-кнопки
- [ ] 9.2 Jira: задачі вантажаться; тогл `is_watched` персиститься
- [ ] 9.3 Tempo: зведення; масовий синк вибраних; кроки конвеєра
- [ ] 9.4 Журнал: фільтри; деталі payload/result/error; verify → `verified`
- [ ] 9.5 Users: створити (запросити) → з'являється; запрошений входить через
  Google за e-mail; deactivate блокує вхід; delete прибирає
- [ ] 9.6 Дубль e-mail у `POST /users` → `409`
