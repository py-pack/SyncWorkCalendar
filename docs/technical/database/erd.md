# Database — ER Diagrams (Mermaid)

Візуальний компаньйон до [schema.md](schema.md). Усі діаграми — Mermaid,
рендеряться напряму в GitHub-preview, PyCharm Markdown plugin і Obsidian.

> **FK constraint-ів у БД нема.** Стрілки нижче — це **логічні** зв'язки,
> що тримаються кодом (DAO, event-listeners, ручні join-и). Деталі — §8
> у [schema.md](schema.md).

---

## 1. Entity-Relationship Diagram

Усі 8 доменних таблиць + 2 API-таблиці. Системна `alembic_version` опущена.

```mermaid
erDiagram
    tc_projects ||--o{ tc_entries : "tc_project_id"
    tc_projects }o..o| jr_issues : "issue_key (fallback)"

    jr_projects ||--o{ jr_issues : "jr_project_id"
    jr_issues ||--o{ jr_worklogs : "jr_issues_id"
    jr_issues ||--o{ key_templates : "issue_key"
    jr_issues }o--o| jr_issues : "epic_key / parent_key (self)"

    jr_users ||--o{ jr_issues : "jr_creator_key / jr_reporter_key"
    jr_users ||--o{ jr_worklogs : "jr_worker_key"
    jr_users ||--o{ worklog_sync_tasks : "worker_key"

    tc_entries ||--o{ worklog_sync_tasks : "source_id"
    jr_worklogs |o--o| worklog_sync_tasks : "target_id"
    jr_issues ||--o{ worklog_sync_tasks : "issue_id / issue_key"

    tc_projects {
        int id PK
        varchar name UK
        int parent_id
        int user_id
        smallint level
        boolean is_archived
        boolean is_sync "локальний прапор"
        varchar issue_key "fallback Jira key"
        varchar color
        timestamptz created_at
        timestamptz updated_at
    }

    tc_entries {
        int id PK
        int tc_project_id "soft FK → tc_projects.id"
        varchar description "→ meta.task"
        json meta
        timestamp start_at "БЕЗ TZ"
        timestamp end_at "БЕЗ TZ"
        int duration "GENERATED STORED"
        timestamptz updated_at
    }

    jr_projects {
        int id PK
        varchar key UK
        varchar name
        boolean is_archved "⚠ typo"
        boolean is_watched
    }

    jr_users {
        int id PK
        varchar key UK
        varchar name
        varchar full_name
        varchar email
    }

    jr_issues {
        int id PK
        varchar key UK
        varchar name
        int jr_project_id "soft FK"
        varchar epic_key
        varchar parent_key
        varchar type
        varchar priority
        varchar status
        varchar jr_creator_key
        varchar jr_reporter_key
        int estimate_plan "seconds"
        int estimate_fact "seconds"
        int estimate_rest "seconds"
        timestamptz created_at
        timestamptz updated_at
    }

    jr_worklogs {
        int id PK
        int jr_issues_id "⚠ ім'я з зайвою s"
        varchar description "→ meta"
        json meta
        varchar jr_worker_key
        timestamptz started_at
        int duration "seconds"
        timestamptz created_at
        timestamptz updated_at
    }

    worklog_sync_tasks {
        int id PK
        enum status "worklog_sync_status_task_enum"
        int source_id "→ tc_entries.id"
        int target_id "→ jr_worklogs.id (після створення)"
        varchar worker_key
        varchar issue_key
        int issue_id
        varchar content "sync|HH:MM|HH:MM - <desc>"
        timestamptz started_at
        int time_spent "seconds"
        timestamptz created_at
        timestamptz updated_at
    }

    key_templates {
        int id PK
        varchar issue_key "цільовий Jira key"
        varchar template "/regex/ або substring"
    }

    api_users ||..o{ api_jobs : "username (created_by / verified_by)"

    api_users {
        int id PK
        varchar username UK
        varchar password_hash "bcrypt"
        varchar worker_key "Jira key, у JWT-claim"
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    api_jobs {
        uuid id PK "gen_random_uuid()"
        varchar trigger_name "sync.timecamp.entries"
        enum status "api_job_status_enum"
        jsonb payload
        jsonb result
        text error
        varchar created_by "→ api_users.username"
        varchar verified_by "→ api_users.username"
        timestamptz started_at
        timestamptz finished_at
        timestamptz verified_at
    }
```

### Легенда кардинальностей

| Notation        | Зміст                                   |
| --------------- | --------------------------------------- |
| `\|\|--o{`       | 1 обов'язкове → 0..N                    |
| `\|o--o\|`       | 0..1 → 0..1                             |
| `}o--o\|`        | 0..N → 0..1                             |
| `}o..o\|` (--..--) | м'який зв'язок через текстовий key (не id) |

---

## 2. Потік даних (data flow)

Хто наповнює які таблиці, і куди витікає synced worklog.

```mermaid
flowchart LR
    TC[TimeCamp API]
    JR[Jira API]
    TEMPO[Tempo API]

    subgraph TC_domain["TimeCamp домен"]
        tcp[(tc_projects)]
        tce[(tc_entries)]
        kt[(key_templates)]
    end

    subgraph JR_domain["Jira домен"]
        jrp[(jr_projects)]
        jru[(jr_users)]
        jri[(jr_issues)]
        jrw[(jr_worklogs)]
    end

    subgraph SYNC["Sync домен"]
        wst[(worklog_sync_tasks)]
    end

    TC -- "GET tasks"   --> tcp
    TC -- "GET entries" --> tce

    JR -- "api/2/project" --> jrp
    JR -- "api/2/search"  --> jri
    JR --                 --> jru

    TEMPO -- "GET worklogs"  --> jrw
    wst   -- "POST worklog (Tempo)" --> TEMPO
    TEMPO -- "id у відповіді" --> wst

    tce -. "source_id" .-> wst
    jrw -. "target_id" .-> wst
    jri -. "issue_id / issue_key" .-> wst

    tce -. "description → meta.task" .-> kt
    kt  -. "match issue_key" .-> tce

    tcp -. "is_sync=TRUE filter" .-> wst
```

Суцільні стрілки — реальні HTTP-виклики або writes у БД. Пунктирні —
логічні зв'язки/lookups усередині застосунку.

---

## 3. State machine — `worklog_sync_status_task_enum`

```mermaid
stateDiagram-v2
    [*]         --> pre_create     : SyncTask.create()
    pre_create  --> create         : WorllogSyncTask.before_create
    create      --> created        : Tempo POST success\n(target_id присвоєно)

    state "pre_update" as pre_update
    state "update" as update
    state "updated" as updated
    state "sync" as sync

    note right of pre_update
        Зарезервовані значення enum-у,
        у поточному коді не використовуються
    end note

    pre_update  --> update
    update      --> updated
```

Деталі переходів — `src/models/worklog_sync_task.py` + хук
`WorllogSyncTask.before_create` / `create_worklogs`.

---

## 3a. State machine — `api_job_status_enum`

```mermaid
stateDiagram-v2
    [*]                  --> running             : POST /sync/** (auth + validate OK)
    running              --> needs_verification  : task завершується без exception
    running              --> failed              : task піднімає exception
    needs_verification   --> verified            : POST /api-jobs/{id}/verify
    verified             --> [*]
    failed               --> [*]
```

`verified` і `failed` — final-стани. Із `needs_verification` повторити синк
не можна — для повтору викликається той самий sync-endpoint, що створює нову
job-row. Деталі — `src/api/jobs_wrapper.py` + `src/dao/api_job_dao.py`.

---

## 4. Як рендерити

- **GitHub** — рендерить Mermaid автоматично в `.md` файлах.
- **PyCharm** — потрібен plugin **Mermaid** (Settings → Plugins). Після
  встановлення Markdown-превʼю показує діаграми.
- **Obsidian / VS Code** — теж є вбудована підтримка.
- **CLI/export** — `mmdc -i erd.md -o erd.svg` (npm-пакет
  `@mermaid-js/mermaid-cli`).

Не редагуй PNG/SVG експорти руками — джерело завжди тут, у `.md`.
