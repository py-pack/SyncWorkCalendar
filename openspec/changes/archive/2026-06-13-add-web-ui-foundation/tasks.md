## 1. Backend — БД та конфіг для Google-входу

- [x] 1.1 Додати колонку `email` (`String`, `UNIQUE`, `nullable=True`) у
  модель `app/models/api_user.py`
- [x] 1.2 `alembic revision --autogenerate -m "add_email_to_api_users"`,
  перевірити згенероване, `alembic upgrade head`
- [x] 1.3 Розширити `APIConfig` (`app/config.py`): `google_client_id: str = ""`,
  `google_client_secret: str = ""` (secret обовʼязковий для `code`-гілки,
  лишається тільки в backend-env); додати у `.env.template` з поясненнями
- [x] 1.4 `app/dao/api_user_dao.py`: `get_by_email(email)` —
  регістронезалежний пошук активного користувача (порівняння у нижньому
  регістрі)

## 2. Backend — `POST /auth/google` (capability `api-google-auth`)

- [x] 2.1 Додати залежність `google-auth` (перевірка Google ID-token)
- [x] 2.2 `app/api/schemas/auth.py`: `GoogleAuthRequest` (рівно одне з
  `credential` або `code`), reuse `TokenResponse`
- [x] 2.3 `app/api/auth.py`: `verify_google_credential(id_token)` —
  верифікація підпису/`aud`/`iss`/`exp`/`email_verified`; для `code` —
  обмін у Google (`GOOGLE_CLIENT_SECRET`) → ID-token
- [x] 2.4 `app/api/routers/auth.py`: `POST /auth/google` — верифікувати,
  дістати e-mail, `get_by_email`, видати наш JWT (ті самі claims, що логін);
  невідомий/неактивний → `401 "account not found"`; немає
  `GOOGLE_CLIENT_ID` → `503`
- [x] 2.5 Маршрут лишити **публічним** (як `/auth/login`) у переліку
  no-auth шляхів
- [x] 2.6 Оновити `docs/technical/api-reference.md` — секція Google-вхід

## 3. Frontend — дизайн-система (capability `web-design-system`)

- [x] 3.1 Перенести CSS-токени і теми з прототипу у `front/src/styles/`
  (`tokens.css`, `themes.css`): світла/темна, акценти, щільність
- [x] 3.2 Підключити шрифти `Geist` + `Geist Mono`
- [x] 3.3 Helper палітри проектів (`projectColors(hue)` → oklch-набір) у
  `front/src/styles/palette.ts`
- [x] 3.4 Компонент `Icon.vue` із набором SVG-шляхів (із прототипу)
- [x] 3.5 UI-примітиви у `front/src/components/ui/`: `Btn`, `IconBtn`,
  `Badge`, `Toggle`, `Checkbox`, `Segmented`, `Avatar`, `Menu`, `Sheet`,
  `Spinner`, `Field`
- [x] 3.6 Панель `TweaksPanel.vue` (акцент, щільність, workBand, weekends)

## 4. Frontend — i18n UK/EN

- [x] 4.1 Перенести словник рядків (`STRINGS.uk` / `STRINGS.en`) у
  `front/src/i18n/strings.ts`
- [x] 4.2 Composable `useI18n()` поверх `ui.lang`; перемикач мови
- [x] 4.3 Перевірити, що видимі підписи беруться зі словника (без хардкоду)

## 5. Frontend — stores та клієнт

- [x] 5.1 `lib/storage.ts`: dot-path обгортка над `localStorage` — `get`/`set`/
  `remove` за ключами через крапку (`ui.theme`, `auth.token`), JSON під одним
  namespaced-ключем, безпечний парсинг (битий JSON → дефолт); єдина точка
  персистенсу для ui- і auth-сторів (D7)
- [x] 5.2 `stores/ui.ts` (Pinia): `theme`, `lang`, `accent`, `density`,
  `workBand`, `weekends`, `navCollapsed`, `route`; синк у `localStorage`
  **через `lib/storage`**; застосування `data-theme` і токенів акценту
- [x] 5.3 `stores/auth.ts`: `token` (персист через `lib/storage`, ключ
  `auth.token`), `currentUser`, `login()`, `loginWithGoogle()`, `refresh()`,
  `logout()`, getters `isAuthed`
- [x] 5.4 Розширити `api/client.ts`: заголовок `Authorization: Bearer`,
  методи `login`, `refresh`, `me`, `google`; типи у `api/types.ts`
- [x] 5.5 Обробка `401` → очищення сесії і показ екрана входу

## 6. Frontend — app shell (capability `web-app-shell`)

- [x] 6.1 `components/AppShell.vue`: ліва навігація (3 секції,
  згортання), головна область, футер з перемикачами теми/мови
- [x] 6.2 `components/UserChip.vue`: аватар + ім'я + `worker_key`, меню
  (профіль/налаштування/вихід)
- [x] 6.3 Оновити `router/index.ts`: маршрути `calendar`, `timecamp`,
  `jira`, `tempo`, `journal`, `users`; тимчасові заглушки-views для фаз 2–3
- [x] 6.4 Auth-gate: navigation guard / умовний рендер — без сесії показувати
  `AuthView`; відновлення останнього маршруту; `/` → `calendar`
- [x] 6.5 Бейдж на пункті Журналу (лічильник `needs_verification`) —
  статичний бейдж із nav-конфіга; живий лічильник прийде з екраном журналу
  (фаза 3, `add-data-screens`)

## 7. Frontend — екран входу (capability `web-auth`)

- [x] 7.1 `views/AuthView.vue`: лого, поля логін/пароль, «запам'ятати»,
  кнопка «Увійти», нотатка про відсутність реєстрації, перемикачі теми/мови
- [x] 7.2 Сабміт логіну → `auth.login()`; стани loading/disabled; помилка
  `401` без розкриття деталей
- [x] 7.3 Підключити Google Identity Services (`gsi/client`,
  `VITE_GOOGLE_CLIENT_ID`); кнопка Google (popup, `ux_mode: 'popup'`) →
  `auth.loginWithGoogle()`
- [x] 7.4 Google **One Tap** (`prompt`) → той самий обробник
- [x] 7.5 Env/Google-конфіг: `VITE_GOOGLE_CLIENT_ID` у
  `front/.env.example`/`.env.development`; authorized JS origins
  `https://sync.dev` у Google Cloud Console (HTTPS — вимога One Tap, D8)

## 8. Документація і Memory Bank

- [x] 8.1 `decisinLog.md`: рішення про Google match-by-email без
  авто-реєстрації (єдиний JWT) + колонка `api_users.email` (D-013)
- [x] 8.2 `docs/technical/database/schema.md`: колонка `email` (+ head
  `c03728fbb1cf`); також `api-reference.md` — секція Google-вхід
- [x] 8.3 `activeContext.md` / `progress.md`: фаза 1 веб-UI реалізована

## 9. Ручний QA

> Автоматично верифіковано: backend `503`/`422`/`401` + `code`-без-secret `503`
> (живий стек + TestClient); `vue-tsc`+`vite build` чисто; front→api проксі OK.
> Решта — інтерактивний браузерний QA (Google-пункти потребують реального
> `VITE_GOOGLE_CLIENT_ID` і authorized origin `https://sync.dev`).

- [x] 9.1 Логін/пароль через екран входу → оболонка з навігацією
- [x] 9.2 Перемикання теми/мови/акценту/щільності — зберігається після
  перезавантаження
- [x] 9.3 Google popup-вхід (валідний e-mail у `api_users`) → вхід
- [x] 9.4 Google вхід із невідомим e-mail → `401`, повідомлення на екрані
- [x] 9.5 One Tap показується за активної Google-сесії і логінить
- [x] 9.6 `GOOGLE_CLIENT_ID` порожній → `POST /auth/google` дає `503`;
  `code`-запит без `GOOGLE_CLIENT_SECRET` → `503`; логін/пароль працює
  (verified live + TestClient)
- [x] 9.7 Logout → екран входу; прострочений токен → екран входу
