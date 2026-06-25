## ADDED Requirements

### Requirement: Глобальний тригер реконсиляції через чергу

Система SHALL надавати `POST /sync/reconcile-links` (опційне тіло `{start, end}` —
період активності; без тіла — дефолтний останній період), що **ставить у чергу**
реконсиляцію лінків TimeCamp↔Tempo для `worker_key` із JWT, замість синхронного
виконання. Endpoint MUST вимагати валідний Bearer-токен; якщо `worker_key IS NULL`
у токені — `400 Bad Request` до постановки. Відповідь повертає `job_id` поставленої
задачі.

Цей тригер — серверний еквівалент кнопки «звʼязати/синхронізувати все»: він лише
**ставить завдання в чергу**, а виконання й `api_jobs`-аудит відбуваються у воркері
(capability `async-task-queue`).

#### Scenario: Постановка реконсиляції в чергу

- **WHEN** авторизований клієнт із `worker_key` викликає `POST /sync/reconcile-links`
- **THEN** реконсиляція ставиться в чергу, відповідь містить `job_id`, а виконання
  й оновлення `api_jobs` робить воркер

#### Scenario: Немає worker_key

- **GIVEN** JWT містить `worker_key = null`
- **WHEN** клієнт викликає `POST /sync/reconcile-links`
- **THEN** відповідь `400 Bad Request`; задача в чергу не ставиться

#### Scenario: Без токена

- **WHEN** клієнт викликає `POST /sync/reconcile-links` без `Authorization`
- **THEN** відповідь `401 Unauthorized`
