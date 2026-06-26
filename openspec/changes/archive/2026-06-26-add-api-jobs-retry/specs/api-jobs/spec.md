## ADDED Requirements

### Requirement: Retry failed job endpoint

Система SHALL надавати `POST /api-jobs/{job_id}/retry` (вимагає авторизації), що
**синхронно** повторює одну впавшу job-у:

- Job-а MUST існувати (інакше `404`) і мати `status = failed` (інакше `409` —
  ретраяться лише впалі; `running`/`needs_verification`/`verified` не повторюються).
- Ендпоінт MUST взяти `trigger_name` і збережений `payload` впалої job-и та
  прогнати **ту саму** роботу через спільний реєстр `trigger_name → робота`, який
  перевикористовує наявні sync-обробники (один і той самий код, що й у відповідного
  sync-тригера). Якщо `trigger_name` невідомий реєстру — `422` (`"trigger is not
  retryable"`).
- Ретрай MUST створити **нову** `api_jobs`-джобу (`created_by` = користувач із JWT)
  і прогнати її через життєвий цикл `running → needs_verification` (успіх) або
  `running → failed` (виняток). Стара впала job-а MUST лишитись незмінною в історії.
- Відповідь MUST бути `200 OK` із `APIJobDetail` **нової** job-и — у **обох**
  випадках (успіх і повторне падіння); синхронна невдача роботи MUST NOT давати
  `500` (нова job-а просто матиме `status = failed` зі своїм `error`).

#### Scenario: Перезапуск впалої job-и — успіх

- **GIVEN** job-а `J1` зі `status = failed`, `trigger_name = sync.worklog-tasks.push-to-tempo`
  і збереженим `payload`
- **WHEN** користувач `POST /api-jobs/{J1}/retry`
- **THEN** створюється **нова** job-а `J2` із тим самим `trigger_name`/`payload`,
  прогнана синхронно; відповідь `200 OK` з `APIJobDetail` `J2`
  (`status = needs_verification`); `J1` лишається `failed`

#### Scenario: Перезапуск знову падає

- **GIVEN** впала job-а, чия причина ще не усунена
- **WHEN** користувач `POST /api-jobs/{id}/retry`
- **THEN** нова job-а стає `failed` зі своїм `error`; відповідь `200 OK` з
  `APIJobDetail` нової (впалої) job-и — **не** `500`

#### Scenario: Ретрай не-failed job-и заборонено

- **GIVEN** job-а зі `status = needs_verification` (або `verified`/`running`)
- **WHEN** користувач `POST /api-jobs/{id}/retry`
- **THEN** відповідь `409 Conflict`; жодної нової job-и не створено

#### Scenario: Невідомий тригер не ретраїться

- **GIVEN** впала job-а, чий `trigger_name` відсутній у реєстрі ретраю
- **WHEN** користувач `POST /api-jobs/{id}/retry`
- **THEN** відповідь `422`; жодної нової job-и не створено

#### Scenario: Неіснуюча job-а

- **WHEN** користувач `POST /api-jobs/{невідомий_id}/retry`
- **THEN** відповідь `404 Not Found`

#### Scenario: Анонімний доступ заборонено

- **WHEN** клієнт `POST /api-jobs/{id}/retry` без `Authorization`
- **THEN** відповідь `401 Unauthorized`
