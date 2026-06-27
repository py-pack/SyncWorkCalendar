## ADDED Requirements

### Requirement: WST — явний забезпечений місток TimeCamp↔Tempo

`worklog_sync_tasks` SHALL бути єдиним явним містком між TimeCamp-записом і
Tempo-worklog-ом із цілісністю, забезпеченою на рівні БД:

- `source_id` (= `tc_entries.id`) MUST мати `UNIQUE`-констрейнт — **один** WST на
  один TimeCamp-запис;
- `source_id` MUST NOT мати delete-FK на `tc_entries` — посилання на TimeCamp-запис
  лишається на app-рівні (історія WST не видаляється каскадно при зникненні запису;
  TimeCamp і Tempo — різні сервіси, синхронимо за можливості);
- `target_id` (= `jr_worklogs.id`) MUST мати FK на `jr_worklogs.id` із
  `ON DELETE SET NULL` — коли Tempo-worklog видаляється, посилання занулюється, без
  дангл-лінків.

Ці інваріанти MUST накладатися alembic-ревізією поверх head `69dde0d17ff2` і MUST
співіснувати з повторним синком дзеркал (`tc_entries`/`jr_worklogs`).

#### Scenario: Дубль-WST за source_id заборонено

- **GIVEN** для TimeCamp-запису вже існує `WorklogSyncTask`
- **WHEN** робиться спроба створити другий WST із тим самим `source_id`
- **THEN** БД відхиляє вставку (`UNIQUE`-порушення); другий місток не зʼявляється

#### Scenario: Видалення worklog-а занулює лінк

- **GIVEN** `WorklogSyncTask.target_id` вказує на Tempo-worklog у `jr_worklogs`
- **WHEN** цей рядок `jr_worklogs` видаляється
- **THEN** `WorklogSyncTask.target_id` стає `NULL` (без дангл-посилання), решта полів
  WST не змінюється

#### Scenario: Видалення TimeCamp-запису не зачіпає місток

- **GIVEN** є `WorklogSyncTask` зі `source_id`, що вказує на TimeCamp-запис
- **WHEN** цей `tc_entries`-рядок видаляється (напр. re-sync прибрав відсутній у пулі)
- **THEN** `WorklogSyncTask` **лишається** (немає каскаду; історія не чіпається)

### Requirement: Нормалізація даних перед накладанням констрейнтів

Міграція SHALL спершу привести наявні дані у відповідність до інваріантів, **до**
створення `UNIQUE`/FK (інакше констрейнти впадуть на наявних порушеннях):

- з кожної групи WST за однаковим `source_id` лишити **один** (пріоритет — із
  заповненим `target_id` і найбільш просунутим `status`), решту видалити (це
  **єдине** видалення WST — чистимо саме некоректну, задвоєну історію);
- занулити `target_id`, що не відповідає жодному наявному `jr_worklogs.id`.

Осиротілі за `source_id` WST (без наявного `tc_entries`) MUST NOT видалятися
(історія не чіпається — FK на `source_id` немає). Міграція MUST залогувати кількість
зачеплених рядків. `downgrade` MUST знімати констрейнти (відновлення видалених
задвоєних рядків не передбачено — це чистка некоректних дублів).

#### Scenario: Наявні дублі-WST згортаються перед UNIQUE

- **GIVEN** у БД є два WST з однаковим `source_id`
- **WHEN** застосовується ревізія
- **THEN** лишається один WST на цей `source_id`, після чого `UNIQUE`-констрейнт
  успішно накладається

#### Scenario: Дангл target_id занулюється перед FK

- **GIVEN** є WST, чий `target_id` вказує на неіснуючий `jr_worklogs.id`
- **WHEN** застосовується ревізія
- **THEN** такий `target_id` стає `NULL`, після чого FK `target_id` успішно
  накладається
