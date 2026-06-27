## 1. Модель і констрейнти

- [x] 1.1 `app/models/worklog_sync_task.py`: `source_id` → `unique=True` (БЕЗ FK на
  `tc_entries` — історію не чіпаємо, D3); `target_id` → FK на `jr_worklogs.id`
  (`ondelete="SET NULL"`). Зберегти наявні `index=True`.
- [x] 1.2 Перевірити імена констрейнтів через `naming_convention` (стабільні для
  alembic): `source_id` із `unique=True, index=True` → **унікальний індекс**
  `ix_worklog_sync_tasks_source_id` (як «CREATE UNIQUE INDEX», D5); FK —
  `fk_worklog_sync_tasks_target_id_jr_worklogs` (звірено через
  `WorklogSyncTask.__table__`).

## 2. Alembic-ревізія (поверх `69dde0d17ff2`)

- [x] 2.1 Згенерувати ревізію; **вручну впорядкувати**: data-fix → constraints.
- [x] 2.2 Data-fix у `upgrade` (до констрейнтів): (а) дедуп WST за `source_id`
  (лишити один — з `target_id` і найпросунутішим `status`, решту `DELETE` — **єдине**
  видалення WST, чистка задвоєної історії); (б) `UPDATE target_id=NULL` для дангл
  (`target_id NOT IN (SELECT id FROM jr_worklogs)`). Осиротілі за `source_id` WST
  **не** чіпати. Залогувати кількості.
- [x] 2.3 Накласти `CREATE UNIQUE` на `source_id` і FK `target_id`→`jr_worklogs`
  (`SET NULL`). **FK на `source_id` НЕ накладати.**
- [x] 2.4 `downgrade` — зняти `UNIQUE` + target-FK (data-fix не відновлюється).
- [x] 2.5 `uv run alembic upgrade head` локально; перевірити, що head оновився
  (`7f8e8dbd1589`; data-fix: 0 задвоєних WST, 2040 дангл-`target_id` занулено;
  `alembic check` — без нових операцій).

## 3. Дедуп довіряє лінку

- [x] 3.1 `ReconcileLinksTask._push`/`WorllogSyncTask.push_one`: підтвердити, що
  лінкований WST (`target_id`/`created`) не ре-пушиться (вже так за `status`);
  явно задокументувати «лінк → fallback кортеж» у `find_match`-шляху.
  (`_push` обробляє лише `_ACTIONABLE`={pre_create,create,pre_update,update}, а
  `find_match` кличе лише гілка `status==create`; `push_one` має guard
  `created`/`updated`→`noop`. Документовано у docstring `find_match` + коментар у
  `_push`.)
- [x] 3.2 Переконатися, що `JRWorklogDAO.find_match` лишається лише fallback-ом для
  незв'язаних WST (поведінка незмінна для них) — запит/логіка не змінені, лише
  docstring.

## 4. Сумісність із дзеркалами (перевірка)

- [x] 4.1 Наживо: звичайний re-sync `jr_worklogs` (`POST /sync/jira/worklogs`) за
  період із лінкованими WST — переконатися, що видалення відсутніх worklog-ів
  занулює `target_id` (SET NULL) і **не** спричиняє ре-пуш/дублі.
  **Підтверджено користувачем — працює.**
  **(Live-QA — на користувача:** робить реальний Tempo-pull + мутацію дзеркала.
  DB-серцевину — FK `SET NULL` при видаленні worklog — уже доведено синтетикою 5.1;
  міграція занулила 2040 дангл-`target_id` на реальних даних без помилок. Зануленому
  `created`-WST ре-пуш не загрожує: він не в `_ACTIONABLE`.)
- [x] 4.2 Наживо: re-sync `tc_entries` (`POST /sync/timecamp/entries`) за період із
  активними WST — переконатися, що WST **лишаються** (FK на `source_id` немає, тож
  каскаду бути не може; перевірка-саніті). **Підтверджено користувачем — працює.**
  **(Live-QA — на користувача:** робить реальний TimeCamp-pull + мутацію дзеркала.
  Відсутність каскаду на `source_id` уже доведено синтетикою 5.1(c) — видалення
  `tc_entry` лишає WST недоторканим.)

## 5. Верифікація

- [x] 5.1 На синтетиці: спроба двох WST з тим самим `source_id` → `UNIQUE`-помилка;
  видалення `jr_worklog` → `target_id` занулюється; видалення `tc_entry` → WST
  **лишається** (без каскаду). Прибрати синтетику. (Усі 3 — **PASS**; виконано в
  одній транзакції з `ROLLBACK`, тож реальні дані не чіпались — синтетики в БД не
  лишилось.)
- [x] 5.2 `openspec validate harden-worklog-link --strict` — OK.
- [x] 5.3 Smoke реконсиляції за період — без регресій (create/dedup/relink/update).
  `ReconcileLinksTask().run` за **порожній майбутній період** (нуль зовнішніх
  викликів у Tempo) пройшов чисто проти нової схеми: `{created:0, relinked:0,
  remarked:0, deduped:0, updated:0, skipped:0, auto_push:True}`, без помилок під
  унікальним `source_id`. Структурно безпечно: `_upsert_links` апдейтить наявний
  WST за `source_id` (ніколи не вставляє дубль). Data-bearing live-прохід (реальні
  Tempo-записи) — частина live-QA 4.1.
