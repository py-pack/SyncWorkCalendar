## Context

Бекенд REST API вже працює (`add-rest-api`): JWT-логін/пароль поверх
`api_users`, захищені роути, журнал `api_jobs`. Фронт — порожній каркас Vue 3
+ Vite + TS (`frontend-app`): один `HomeView`, `fetch`-клієнт лише з
`getHealth()`, один Pinia-store. Дизайн **Sync Work** прийшов як прототип на
React (UMD + Babel у браузері) — його треба **перенести в Vue**, відтворивши
візуал, а не структуру прототипу (так вимагає README handoff-бандла).

**Джерело дизайну (локально):** прототип лежить у `docs/design/` (ідентичний
handoff-бандлу з Claude Design). Звірятися поекранно з
`docs/design/project/src/*` і `docs/design/project/Sync Work.html`. Для цієї
зміни релевантні: `styles.css` (токени/теми), `ui.jsx` (примітиви+іконки),
`auth.{jsx,css}` (екран входу), `app.jsx` (shell/навігація/auth-gate),
`data.jsx` (i18n-словник), `tweaks-panel.jsx` (Tweaks).

Ця зміна — **фаза 1 із трьох** (далі `add-calendar-timesheet`,
`add-data-screens`). Вона будує спільний фундамент і авторизацію, зокрема
нову вимогу — **вхід через Google** з прив'язкою до наявних `api_users`.

Обмеження: пакетний менеджер фронта — `npm`; HTTP-клієнт — рідний `fetch`
(без `axios`, рішення D-012); стан — Pinia; бекенд-команди — з `api/`.

## Goals / Non-Goals

**Goals:**

- Дизайн-токени + теми (світла/темна) + щільність + 5 акцентів як CSS
  custom properties, керовані з Pinia і `localStorage`.
- Обгортка над `localStorage` (dot-path, як міні-БД) — єдина точка
  персистенсу UI-налаштувань і токена сесії.
- Повний набір Vue UI-примітивів та іконок, придатний для фаз 2–3.
- i18n UK/EN зі словником рядків (із прототипу) і перемикачем.
- App shell: навігація, маршрути на 7 екранів, auth-gate, user-chip, Tweaks.
- Екран входу: логін/пароль (наявний API) + Google popup + One Tap.
- Backend `POST /auth/google`: серверна верифікація, match-by-email, видача
  нашого JWT, без авто-реєстрації; колонка `api_users.email`.

**Non-Goals:**

- Самі екрани календаря/таблиць/журналу/користувачів (фази 2–3) — у цій
  зміні вони можуть бути порожніми заглушками-роутами.
- RBAC-ролі і per-user OAuth-токени на Jira/TimeCamp (окремі майбутні зміни).
- Users CRUD через API (фаза 3) — поки e-mail користувача проставляється
  CLI/ручним INSERT.
- Реальний «forgot password» флоу (посилання є, бекенду немає).

## Decisions

### D1 — Google-флоу: серверна верифікація, match-by-email, без авто-реєстрації

За вимогою користувача Google використовується **тільки для аутентифікації
особи**, не для реєстрації. Фронт отримує від Google **ID-token** (One Tap /
GIS `credential`) або **auth-code** (popup), і відправляє на `POST /auth/google`.
Бекенд **верифікує серверно** (бібліотека `google-auth`: перевірка підпису
через Google JWKS, `aud == GOOGLE_CLIENT_ID`, `iss`, `exp`, `email_verified`),
дістає e-mail, шукає активного `api_users` за `email` (lower-case) і видає наш
**звичайний JWT** — той самий, що й логін/пароль (claims `sub`, `user_id`,
`worker_key`, `exp`, `iat`). Невідомий/неактивний e-mail → `401` без
створення рядка.

- **Чому єдиний JWT:** решта застосунку (auth-gate, refresh, worker_key для
  синку) уже працює на нашому JWT. Google — лише альтернативний спосіб
  довести особу; після входу сесія однакова.
- **Чому серверна верифікація:** клієнту не можна довіряти e-mail; підпис
  Google перевіряється на бекенді.
- **Альтернативи:** *повний server-side redirect OAuth* (відкинули — користувач
  явно хоче popup + One Tap, фронт-центричний флоу); *авто-провіжн нового
  юзера* (відкинули — суперечить «реєстрацію робить адмін»).

### D2 — Підтримати і `credential`, і `code` в одному endpoint

One Tap і GIS-кнопка в режимі `credential` повертають **ID-token** одразу —
його достатньо для match-by-email. Popup у режимі auth-**code** повертає код,
який бекенд обмінює в Google на токени (потрібен `GOOGLE_CLIENT_SECRET`) і
бере ID-token. `POST /auth/google` приймає рівно одне з полів `{credential}`
або `{code}`. Це покриває обидва UX зі скріна (кнопка + One Tap) одним
контрактом.

**Рішення (resolved):** обидві Google-гілки — **в скоупі**, не опційні. За
вимогою користувача мають працювати всі **три** способи входу (логін/пароль,
Google popup → `code`, Google One Tap → `credential`), і всі вони повертають
**один і той самий** наш JWT, згенерований на бекенді (див. D1). Тому
`GOOGLE_CLIENT_SECRET` **обовʼязковий** на деплої (потрібен для обміну `code`),
а не «вимикач» гілки.

### D3 — Колонка `api_users.email UNIQUE NULL` + нормалізація

Зараз `api_users` не має e-mail. Додаємо `email` (`UNIQUE`, nullable, бо старі
рядки можуть бути без нього). Зіставлення — регістронезалежне (зберігати/
порівнювати у нижньому регістрі). Одна alembic-ревізія. Без e-mail
Google-вхід для користувача неможливий — це очікувано (адмін має заповнити
e-mail).

### D4 — Перенесення React-прототипу у Vue 1:1 за візуалом

Прототип — React+Babel у браузері. Переносимо в ідіоматичний Vue 3
(`<script setup>` + SFC), зберігаючи **візуал і поведінку**, але не копіюючи
React-структуру. UI-примітиви стають Vue-компонентами у `components/ui/`.
CSS прототипу (токени, теми, класи) переносимо майже як є — він фреймворк-
незалежний. i18n-словник переноситься напряму.

- **Альтернатива:** автоматичний React→Vue (відкинули — прототип не для
  продакшну, ручний порт чистіший).

### D5 — Стейт і персистенс через Pinia + `localStorage`

Три stores: `auth` (token, currentUser, login/google/refresh/logout),
`ui` (theme, lang, accent, density, workBand, weekends, navCollapsed, route),
плюс i18n-composable поверх `ui.lang`. UI-налаштування синхронізуються в
`localStorage` (як у прототипі через `useStored`). Токен зберігається у
`localStorage` (single-user внутрішній інструмент; XSS-поверхня мінімальна).

- **Альтернатива:** httpOnly-cookie для токена (відкинули на цей етап —
  бекенд віддає Bearer-JWT, cookie-флоу — окрема зміна, якщо знадобиться).

### D6 — Google SDK на фронті

Підключаємо Google Identity Services (`https://accounts.google.com/gsi/client`)
скриптом, ініціалізуємо One Tap і `renderButton`/`prompt` з
`VITE_GOOGLE_CLIENT_ID`. Без важкого npm-пакета; за потреби — тонка обгортка.
`ux_mode: 'popup'`.

### D7 — Обгортка над `localStorage` з dot-path доступом

Замість прямих звернень до `localStorage` вводимо тонку **типизовану
обгортку** (`front/src/lib/storage.ts`), яка поводиться як маленька БД над
одним JSON-документом: ключі через крапку адресують вкладені поля —
`get('ui.theme')`, `set('ui.accent', '#2a6fdb')`, `remove('auth.token')`. Під
капотом — JSON-серіалізація під одним namespaced-ключем, безпечний парсинг
(битий JSON → дефолт, без винятку), реактивний міст до Pinia (аналог
прототипного `useStored`). Це **єдина точка доступу** і для UI-налаштувань
(`web-app-shell`), і для токена сесії (`web-auth`).

- **Чому:** прибирає розсипані `JSON.parse/stringify`, дає однаковий dot-path
  контракт усім сторам і спрощує майбутню міграцію сховища (cookie/IndexedDB) —
  змінюється лише адаптер обгортки, а не виклики у сторах.
- **Альтернатива:** прямий `localStorage` per-ключ (відкинули — користувач
  явно попросив обгортку з вкладеними ключами).

### D8 — Домени Google-origins і розподіл env між фронтом і беком

**Authorized JS origins** (Google Cloud Console) і домен фронта для One Tap —
**`https://sync.dev`** на dev (прод-домен додається пізніше). Саме `sync.dev`,
бо Google вимагає **HTTPS** для не-`localhost` origins і для One Tap — під це
вже налаштований host-nginx із довіреним cert (`techContext.md`). `sync.loc`
(http) лишається для звичайної роботи, але Google-кнопка/One Tap працюють із
https-origin.

**Розподіл env (секрет не тече у фронт):**

- Фронт отримує **тільки публічний** `VITE_GOOGLE_CLIENT_ID` (потрапляє у
  бандл — це нормально, client_id не секрет).
- Бек тримає `APP__API__GOOGLE_CLIENT_ID` і **`APP__API__GOOGLE_CLIENT_SECRET`**:
  secret **ніколи** не збирається у фронт-бандл і не віддається клієнту.
- App↔API — один origin за host-nginx/Vite-проксі (`/` фронт, `/api` бек),
  тож CORS для власних запитів застосунку не потрібен; `APP__API__CORS_ORIGINS`
  лишається для прямих (не через проксі) звернень за потреби.

## Risks / Trade-offs

- **[Немає e-mail у `api_users` → Google-вхід не працює для користувача]** →
  Mitigation: документуємо, що адмін заповнює e-mail; до Users CRUD (фаза 3)
  — через CLI/INSERT. Логін/пароль завжди лишається запасним шляхом.
- **[Токен у `localStorage` (XSS)]** → Mitigation: внутрішній single-user
  інструмент, строгий CSP можливий пізніше; cookie-флоу винесено в окрему
  зміну за потреби.
- **[`GOOGLE_CLIENT_SECRET` для code-флоу]** → `code`-гілка в скоупі (D2), тож
  secret **обовʼязковий** на деплої. Mitigation: secret живе лише в backend-env
  (`APP__API__GOOGLE_CLIENT_SECRET`), не потрапляє у фронт-бандл (D8); якщо
  secret не заданий — `code`-запит дає `503` (як і відсутній `GOOGLE_CLIENT_ID`),
  а `credential`-гілка й логін/пароль працюють.
- **[Розбіжність візуалу React→Vue]** → Mitigation: звіряємося з джерелом
  прототипу (`docs/design/project/src/*`) поекранно; CSS переноситься як є.
- **[Заглушки маршрутів фаз 2–3]** → Mitigation: тимчасові порожні views,
  які замінять `add-calendar-timesheet` і `add-data-screens`.

## Migration Plan

1. Backend: alembic-ревізія `add_email_to_api_users` (`email UNIQUE NULL`) →
   `alembic upgrade head`.
2. Backend: `google-auth` у залежності; `APIConfig.google_client_id/secret`
   (secret обовʼязковий для `code`-гілки, лише backend-env); `.env.template`.
   `POST /auth/google` + `APIUserDAO.get_by_email`.
3. Frontend: storage-обгортка (dot-path над `localStorage`, D7) → дизайн-
   система (токени/теми/примітиви/іконки/i18n/Tweaks) → shell → екран входу
   (пароль → Google → One Tap).
4. Конфіг Google: OAuth client у Google Cloud, authorized JS origins
   `https://sync.dev` (+ прод пізніше); `VITE_GOOGLE_CLIENT_ID` у фронт-env,
   `GOOGLE_CLIENT_ID`/`SECRET` у backend-env.
5. Ручний QA: логін/пароль; Google popup; One Tap; невідомий e-mail → `401`;
   `503` коли `GOOGLE_CLIENT_ID` порожній.

Rollback: прибрати `POST /auth/google` і фронт-кнопку; колонка `email`
лишається (безпечна, nullable). Логін/пароль не зачеплено.

## Open Questions

*Усі попередні відкриті питання вирішені під час уточнення з користувачем —
рознесені у Decisions:*

- **Code-флоу (`GOOGLE_CLIENT_SECRET`) чи лише `credential`?** → **Обидві**
  Google-гілки в скоупі; мають працювати всі три способи входу, і всі віддають
  єдиний JWT з бекенду; `GOOGLE_CLIENT_SECRET` обовʼязковий (D1, D2).
- **Домени фронта для Google origins і CORS?** → `https://sync.dev` на dev
  (HTTPS під One Tap); env розділено фронт/бек, secret не тече у фронт; CORS для
  власних запитів не потрібен — один origin за host-nginx/Vite-проксі (D8).
- **`localStorage` чи cookie для токена?** → Лишаємо `localStorage`, але через
  спільну **dot-path обгортку** як єдину точку доступу; перехід на інше сховище
  стане заміною адаптера, не виклику (D5, D7).
