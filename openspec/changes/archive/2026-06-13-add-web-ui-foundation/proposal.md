## Why

Бекенд REST API вже піднято (`add-rest-api`), а фронтенд лишається порожнім
каркасом: `front/` має тільки `HomeView`, health-store і один маршрут. Дизайн
**Sync Work** (handoff із Claude Design) описує цілісний веб-інтерфейс на 7
екранів зі спільною оболонкою, дизайн-системою, двомовністю та двома темами.
Перш ніж будувати окремі екрани (календар, таблиці, журнал, користувачі),
потрібен **фундамент**: дизайн-токени, набір UI-примітивів, i18n, тема, app
shell і екран авторизації. Це перша з трьох фаз перенесення дизайну в код.

Окремо авторизація має закрити нову вимогу — **вхід через Google** (popup +
One Tap) із прив'язкою до існуючих `api_users` за e-mail (без самостійної
реєстрації).

## What Changes

- **Дизайн-система (frontend):** дизайн-токени (шрифти `Geist`/`Geist Mono`,
  акцент `#2a6fdb` + 4 альтернативи, oklch-палітра проектів, світла/темна
  теми, щільність `compact`/`regular`), портовані у Vue UI-примітиви
  (`Btn`, `IconBtn`, `Badge`, `Toggle`, `Checkbox`, `Segmented`, `Avatar`,
  `Menu`, `Sheet`, `Spinner`, `Field`, `Icon` із набором SVG), та панель
  **Tweaks** (акцент, щільність, смуга робочих годин, вихідні).
- **i18n UK/EN:** легкий механізм перекладів (словник рядків зі скріна
  дизайну) із перемикачем мови; мова й тема зберігаються у `localStorage`
  через спільну **dot-path обгортку** (єдина точка персистенсу і для токена).
- **App shell:** ліва навігація (3 секції — Трекінг / Дані / Адміністрування,
  згортувана), клієнтська маршрутизація на всі 7 екранів, перемикачі
  мови/теми, user-chip з меню (профіль/налаштування/вихід), **auth-gate**
  (неавторизований бачить лише екран входу).
- **Екран авторизації (frontend):** логін/пароль + кнопка Google + Google
  **One Tap**, нотатка «реєстрація недоступна», обробка стану входу
  (зберігання JWT, logout, авто-рефреш токена).
- **Google-вхід (backend):** новий endpoint `POST /auth/google`, що приймає
  Google-credential (One Tap **ID token**) або auth-**code** з popup-флоу,
  верифікує його в Google, дістає e-mail і **зіставляє з `api_users.email`**.
  Якщо активний користувач із таким e-mail існує — видається наш звичайний
  JWT (ті самі claims, що й при логіні/паролі). Невідомий e-mail → `401`.
  **Без авто-створення користувачів.**
- **Зміни в БД:** додати колонку `api_users.email` (`UNIQUE`, nullable) —
  потрібна для зіставлення Google-акаунта. Одна alembic-ревізія.
- **Конфігурація:** додати `APP__API__GOOGLE_CLIENT_ID` (і
  `GOOGLE_CLIENT_SECRET` для обміну auth-code) у `APIConfig` та
  `.env.template`; передати `VITE_GOOGLE_CLIENT_ID` у фронт.
- Бізнес-логіка синку, доменні моделі (`tc_*`, `jr_*`, `worklog_sync_tasks`)
  і наявні `/auth/login|refresh|me` **не змінюються** — логін/пароль працює
  як був, Google-вхід додається поряд.

Без breaking-змін у наявному API: додаємо новий endpoint і колонку, не чіпаючи
наявні контракти.

## Capabilities

### New Capabilities

- `web-design-system`: дизайн-токени, теми (світла/темна), щільність,
  набір Vue UI-примітивів та іконок, панель Tweaks, i18n UK/EN — спільний
  фундамент для всіх екранів.
- `web-app-shell`: оболонка застосунку — навігація, маршрутизація на 7
  екранів, перемикачі теми/мови, user-chip, auth-gate, персистенс
  UI-налаштувань у `localStorage`.
- `web-auth`: екран входу (логін/пароль + Google + One Tap) і клієнтське
  керування сесією (зберігання токена, авто-рефреш, logout).
- `api-google-auth`: backend-верифікація Google-credential/коду, зіставлення
  за e-mail із `api_users`, видача нашого JWT без авто-реєстрації.

### Modified Capabilities

- `frontend-app`: наявна вимога маршрутизації («щонайменше один маршрут,
  кореневий рендерить `App.vue`») розширюється до **auth-gated** оболонки з
  маршрутами на всі екрани; базові Pinia-stores стають реальними (auth, UI,
  i18n).

## Impact

- **Новий код (frontend):** `front/src/` — `lib/storage.ts` (dot-path обгортка
  над `localStorage`), `styles/` (токени, теми), `components/ui/*` (примітиви),
  `components/AppShell.vue`, `views/AuthView.vue`, `i18n/` (словник +
  composable), `stores/auth.ts`, `stores/ui.ts`, `api/client.ts` (розширення:
  auth-заголовок, login/refresh/me, google), оновлений `router/index.ts`.
  `HomeView` замінюється/редіректить на `calendar`.
- **Новий код (backend):** `app/api/routers/auth.py` — `POST /auth/google`;
  `app/api/auth.py` — верифікація Google-токена (бібліотека
  `google-auth`); `app/api/schemas/auth.py` — `GoogleAuthRequest`;
  `app/dao/api_user_dao.py` — `get_by_email`.
- **БД:** колонка `api_users.email UNIQUE NULL` + одна alembic-ревізія;
  оновити `docs/technical/database/schema.md`.
- **Залежності:** frontend — Google Identity Services (`accounts.google.com`
  скрипт, без npm-пакета) або `vue3-google-login`; backend — `google-auth`
  (перевірка ID-token) + `requests` (обмін code, уже є).
- **Конфігурація:** backend-env `APP__API__GOOGLE_CLIENT_ID`/
  `GOOGLE_CLIENT_SECRET` (secret лишається на беку, не тече у фронт), front-env
  `VITE_GOOGLE_CLIENT_ID`; Google authorized JS origins `https://sync.dev`
  (HTTPS під One Tap). App↔API — один origin за проксі, тож CORS для власних
  запитів не потрібен.
- **Документація:** `docs/technical/api-reference.md` — секція Google-вход;
  Memory Bank (`activeContext.md`, `progress.md`, `decisinLog.md` — рішення
  про match-by-email без авто-реєстрації).
- **Поза скоупом (відкладено):** RBAC-ролі (admin/member/viewer) і
  per-user OAuth-токени на Jira/TimeCamp — окремі майбутні зміни. Календар і
  таблиці/журнал/користувачі — фази 2 і 3 (`add-calendar-timesheet`,
  `add-data-screens`).
- **Ризики:** збіг e-mail Google ↔ `api_users.email` вимагає, щоб адмін
  заповнив e-mail при заведенні користувача; поки `add-data-screens` не дав
  Users CRUD — e-mail проставляється тим же шляхом, що й зараз (CLI/ручний
  INSERT). Mitigation — у `design.md`.
