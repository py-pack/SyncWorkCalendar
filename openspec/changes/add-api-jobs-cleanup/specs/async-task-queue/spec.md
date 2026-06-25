## ADDED Requirements

### Requirement: Планове прибирання журналу `api_jobs`

Система SHALL запускати з `Celery beat` окрему **maintenance**-таску прибирання
`api_jobs`, що за щодобовим розкладом (фіксована константа, після нічних синків —
напр. `02:00` за `APP__CELERY__TIMEZONE`) виконує два кроки:

1. **авто-verify** старих `needs_verification` (старших за `APP__CELERY__AUTO_VERIFY_DAYS`,
   дефолт `7`) → `verified` із `verified_by = "system"`;
2. **TTL-видалення** термінальних (`verified`/`failed`) рядків, старших за
   `APP__CELERY__JOB_TTL_DAYS` (дефолт `90`).

Ця таска MUST **не** створювати власний `api_jobs`-аудит-рядок (на відміну від
sync-тасок) — інакше maintenance плодила б job-и, які сама ж чистить; вона лише
логує кількість авто-verify-нутих і видалених. Per-user `sync_prefs` тут **не**
застосовні (це глобальне прибирання, не per-user синк).

#### Scenario: Щодобовий тік прибирає журнал

- **GIVEN** `beat` запущено
- **WHEN** настає запланований час прибирання
- **THEN** у чергу стає maintenance-таска, яка авто-verify-ить старі
  `needs_verification` і видаляє старі термінальні рядки згідно з налаштованими TTL

#### Scenario: Maintenance-таска не засмічує журнал

- **WHEN** maintenance-таска виконується
- **THEN** у `api_jobs` **не** з'являється новий рядок про саму таску прибирання
