## ADDED Requirements

### Requirement: Авто-реконсиляція лінків TimeCamp↔Tempo

Система SHALL надавати ідемпотентну задачу `reconcile_links(period, worker_key)`,
що для кожного TimeCamp-запису в періоді:

1. визначає поточну задачу матчу (`tc_entries.meta.task` → fallback
   `tc_project.issue_key`);
2. **upsert** `WorklogSyncTask` за `source_id` (немає — створює у `pre_create`;
   є — лишає, але оновлює `issue_key`/`issue_id`, якщо матч змінився);
3. резолвить `issue_id` (підтягуючи відсутні задачі з Jira) і ставить у чергу
   створення/оновлення Tempo-відмітки.

Реконсиляція MUST бути безпечною для повторного запуску (повторний прохід над тими
самими даними не плодить дублів і не змінює вже завершені записи без потреби).

#### Scenario: Новий TimeCamp-запис із метчем

- **GIVEN** є TimeCamp-запис із розпізнаною задачею у `meta.task`, без
  `WorklogSyncTask`
- **WHEN** виконується `reconcile_links` за період цього запису
- **THEN** створюється `WorklogSyncTask` (`source_id` = id запису, `issue_key` =
  матч) і ставиться в чергу пуш у Tempo

#### Scenario: Повторний прохід ідемпотентний

- **GIVEN** для запису вже є `WorklogSyncTask`
- **WHEN** `reconcile_links` запускається ще раз за той самий період
- **THEN** дубль `WorklogSyncTask` для цього `source_id` **не** створюється

### Requirement: Матчинг на створення І на зміну опису; перелінк без авто-відлінку

Реконсиляція MUST враховувати **зміну** опису TimeCamp-запису, а не лише перше
встановлення. Якщо після зміни опису запис матчиться на **іншу** задачу, наявний
`WorklogSyncTask` MUST бути **перелінкований** (оновлюються `issue_key`/`issue_id`,
а за наявності пушу — ініціюється оновлення Tempo-відмітки). Якщо запис після зміни
**не** матчиться на жодну задачу, система MUST NOT автоматично розривати наявний
звʼязок — `WorklogSyncTask` лишається як є.

#### Scenario: Зміна опису → перелінк на іншу задачу

- **GIVEN** `WorklogSyncTask` звʼязаний із задачею `AAA-1`
- **WHEN** опис TimeCamp-запису змінився так, що тепер матчиться `BBB-2`, і
  виконується реконсиляція
- **THEN** `WorklogSyncTask.issue_key` стає `BBB-2`, `issue_id` перерезолвлюється, а
  Tempo-відмітка ставиться в чергу на оновлення

#### Scenario: Опис більше не матчить задачу → звʼязок зберігається

- **GIVEN** `WorklogSyncTask` звʼязаний із задачею `AAA-1`
- **WHEN** опис змінили так, що жодна задача не розпізнається
- **THEN** наявний звʼязок `WorklogSyncTask` **не** розривається автоматично

### Requirement: Дедуп проти наявних Tempo-worklog-ів

Перед створенням worklog-а в Tempo система SHALL звірити кандидата з локальними
`jr_worklogs` за `(jr_issues_id, jr_worker_key, started_at, duration)`. Якщо
відповідний worklog уже існує, система MUST звʼязати `WorklogSyncTask.target_id` із
ним і перевести у `created` **без** повторного HTTP-виклику в Tempo.

#### Scenario: Worklog уже є в Tempo

- **GIVEN** у `jr_worklogs` є запис, що збігається з кандидатом за задачею, worker,
  часом початку і тривалістю
- **WHEN** реконсиляція доходить до пушу цього `WorklogSyncTask`
- **THEN** `target_id` встановлюється на наявний worklog, `status = created`, а
  новий worklog у Tempo **не** створюється

#### Scenario: Збігу немає → створюється новий

- **GIVEN** у `jr_worklogs` немає збіжного запису
- **WHEN** реконсиляція доходить до пушу
- **THEN** виконується створення worklog-а в Tempo, `target_id` = повернутий
  `originId`, `status = created`

### Requirement: Авто-створення або оновлення Tempo-відмітки (`pre_update → update → updated`)

Знайдений метч SHALL доводитись до кінцевого стану автоматично. Якщо
`WorklogSyncTask` ще не запушений — створюється новий Tempo-worklog. Якщо вже
`created` (є `target_id`), але контент/час розійшлися з тим, що в Tempo, — задача
MUST перейти `created → pre_update → update → updated`, виконавши **оновлення**
наявного Tempo-worklog-а. Видалення worklog-ів — поза скоупом (звʼязок не
розривається).

#### Scenario: Зміна вже запушеного запису → оновлення в Tempo

- **GIVEN** `WorklogSyncTask` у статусі `created` з `target_id`
- **WHEN** його контент/час змінились (через зміну опису) і виконується реконсиляція
- **THEN** наявний Tempo-worklog оновлюється, а статус проходить
  `pre_update → update → updated`

#### Scenario: Видалення не виконується автоматично

- **WHEN** TimeCamp-запис зник або перестав матчитись
- **THEN** раніше створений Tempo-worklog **не** видаляється автоматично

### Requirement: Глобальний enqueue-тригер реконсиляції поважає per-user перемикачі

Будь-яка автоматична постановка MUST поважати per-user `sync_prefs` (beat, реакція на витяг, глобальна кнопка «звʼязати все»): за вимкненого `auto_linking` реконсиляція для користувача не ставиться; за вимкненого `auto_push_tempo` реконсиляція може оновити звʼязок, але **не** ініціює створення/оновлення worklog-а в Tempo.

#### Scenario: Вимкнено auto_push_tempo

- **GIVEN** користувач має `auto_push_tempo = false`
- **WHEN** реконсиляція знаходить метч для його запису
- **THEN** `WorklogSyncTask` оновлюється/створюється, але пуш/оновлення в Tempo **не**
  виконується
