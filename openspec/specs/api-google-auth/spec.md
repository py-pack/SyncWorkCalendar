# api-google-auth Specification

## Purpose
TBD - created by archiving change add-web-ui-foundation. Update Purpose after archive.
## Requirements
### Requirement: Google sign-in endpoint

Система SHALL надавати `POST /auth/google`, що приймає тіло з Google-
credential — або `{credential: <ID token>}` (One Tap / GIS credential), або
`{code: <auth code>}` (popup auth-code флоу). Endpoint MUST верифікувати
credential у Google (підпис, термін дії, `aud` == `APP__API__GOOGLE_CLIENT_ID`,
`iss` із Google), дістати e-mail (тільки якщо `email_verified == true`),
знайти активного користувача в `api_users` за цим e-mail і повернути наш JWT
із тими самими claims, що й логін/пароль (`sub`, `user_id`, `worker_key`,
`exp`, `iat`).

#### Scenario: Успішна верифікація credential (One Tap)

- **GIVEN** `api_users` містить активний рядок із `email = "i.petrenko@leadsdoit.io"`
- **WHEN** клієнт `POST /auth/google` з валідним `credential`, чий
  верифікований e-mail — `i.petrenko@leadsdoit.io`
- **THEN** відповідь `200 OK` з тілом `{access_token, token_type: "bearer", expires_in}`,
  claims токена відповідають знайденому користувачу

#### Scenario: Успішна верифікація через auth-code (popup)

- **WHEN** клієнт `POST /auth/google` з валідним `code` із popup-флоу
- **THEN** сервер обмінює `code` на токени в Google, верифікує отриманий
  ID-token і далі діє як у сценарії credential

### Requirement: Google-вхід не створює користувачів

Endpoint `POST /auth/google` MUST NOT створювати рядки в `api_users`. Якщо
верифікований e-mail не відповідає жодному активному користувачу — вхід
відхиляється. Авто-провіжн заборонено (узгоджено з рішенням «реєстрацію
робить адмін»).

#### Scenario: Невідомий e-mail

- **GIVEN** жоден `api_users` не має `email`, що дорівнює верифікованому
  e-mail Google-акаунта
- **WHEN** клієнт `POST /auth/google` з валідним credential
- **THEN** відповідь `401 Unauthorized` із `{detail: "account not found"}`;
  жоден рядок у `api_users` не створюється

#### Scenario: Неактивний користувач

- **GIVEN** `api_users.email` збігається, але `is_active = FALSE`
- **WHEN** клієнт `POST /auth/google` з валідним credential
- **THEN** відповідь `401 Unauthorized` (та сама відповідь, що й для
  невідомого e-mail, щоб не давати розрізнення)

### Requirement: Відхилення невалідного Google-credential

Endpoint MUST повертати `401 Unauthorized`, якщо credential/код невалідний:
прострочений, із неправильним `aud`/`iss`, з непідтвердженим e-mail
(`email_verified == false`) або з пошкодженим підписом. Верифікація MUST
виконуватися серверно проти Google (не довіряти даним клієнта без перевірки).

#### Scenario: Прострочений або підроблений токен

- **WHEN** клієнт `POST /auth/google` з простроченим або непідписаним Google
  ID-token
- **THEN** відповідь `401 Unauthorized`, JWT не видається

#### Scenario: Невірна аудиторія

- **WHEN** `aud` у credential не дорівнює `APP__API__GOOGLE_CLIENT_ID`
- **THEN** відповідь `401 Unauthorized`

#### Scenario: Непідтверджений e-mail

- **WHEN** Google-credential валідний, але `email_verified == false`
- **THEN** відповідь `401 Unauthorized`, вхід не відбувається

### Requirement: Колонка e-mail у `api_users`

Таблиця `api_users` SHALL мати колонку `email` (`UNIQUE`, nullable),
по якій зіставляється Google-акаунт. Зіставлення MUST бути
регістронезалежним за нормалізованим e-mail (порівняння у нижньому регістрі).

#### Scenario: Регістронезалежне зіставлення

- **GIVEN** `api_users.email = "i.petrenko@leadsdoit.io"`
- **WHEN** Google повертає e-mail `I.Petrenko@leadsdoit.io`
- **THEN** користувач знаходиться (порівняння у нижньому регістрі)

### Requirement: Конфіг Google client id/secret

Endpoint `POST /auth/google` MUST повертати `503 Service Unavailable`, якщо
`APP__API__GOOGLE_CLIENT_ID` не заданий (Google-вхід вимкнено), не падаючи з
500. Обмін `code` додатково потребує `APP__API__GOOGLE_CLIENT_SECRET`: якщо
надійшов `{code}`, а secret не заданий, endpoint MUST повертати `503` (не
`500`); `credential`-гілка від наявності secret не залежить. Логін/пароль MUST
лишатися робочим незалежно від наявності Google-конфігу.

#### Scenario: Google не налаштований

- **GIVEN** `APP__API__GOOGLE_CLIENT_ID` порожній
- **WHEN** клієнт `POST /auth/google`
- **THEN** відповідь `503 Service Unavailable`; `POST /auth/login` (логін/
  пароль) при цьому працює нормально

#### Scenario: Code-флоу без secret

- **GIVEN** `APP__API__GOOGLE_CLIENT_ID` заданий, але
  `APP__API__GOOGLE_CLIENT_SECRET` порожній
- **WHEN** клієнт `POST /auth/google` з тілом `{code}`
- **THEN** відповідь `503 Service Unavailable`; запит із `{credential}` і
  логін/пароль працюють нормально

