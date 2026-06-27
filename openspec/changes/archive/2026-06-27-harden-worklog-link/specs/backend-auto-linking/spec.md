## MODIFIED Requirements

### Requirement: Дедуп проти наявних Tempo-worklog-ів

Перед створенням worklog-а в Tempo система SHALL уникати дублів, **спершу довіряючи
явному лінку**, і лише потім — матчингу за кортежем:

- Якщо `WorklogSyncTask` уже має `target_id` (лінкований, статус `created`/`updated`)
  — він MUST NOT пушитись повторно (канонічне «вже представлено» = явний лінк).
- Для ще не лінкованого WST (`pre_create`/`create`) система SHALL звірити кандидата з
  локальними `jr_worklogs` за `(jr_issues_id, jr_worker_key, started_at, duration)`
  — **fallback** для worklog-ів, створених поза конвеєром або осиротілих. Якщо
  відповідний worklog уже існує, система MUST звʼязати `WorklogSyncTask.target_id` із
  ним і перевести у `created` **без** повторного HTTP-виклику в Tempo.

Тобто явний лінк (`target_id`) — джерело правди про звʼязок; кортеж лишається лише
механізмом **виявлення** незв'язаних збігів.

#### Scenario: Уже лінкований WST не пушиться повторно

- **GIVEN** `WorklogSyncTask` має `target_id` і статус `created`
- **WHEN** реконсиляція проходить період
- **THEN** worklog у Tempo **не** створюється повторно (довіра до явного лінку)

#### Scenario: Незв'язаний WST — дедуп за кортежем (fallback)

- **GIVEN** `WorklogSyncTask` без `target_id`, а в `jr_worklogs` є запис, що
  збігається за задачею, worker, часом початку і тривалістю
- **WHEN** реконсиляція доходить до пушу цього WST
- **THEN** `target_id` встановлюється на наявний worklog, `status = created`, новий
  worklog у Tempo **не** створюється

#### Scenario: Збігу немає → створюється новий

- **GIVEN** `WorklogSyncTask` без `target_id`, у `jr_worklogs` немає збіжного запису
- **WHEN** реконсиляція доходить до пушу
- **THEN** виконується створення worklog-а в Tempo, `target_id` = повернутий
  `originId`, `status = created`
