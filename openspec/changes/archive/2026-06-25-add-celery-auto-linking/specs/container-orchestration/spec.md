## ADDED Requirements

### Requirement: Async-стек — сервіси `redis`, `worker`, `beat`

`docker-compose.yml` SHALL додатково описувати сервіси `redis` (брокер черги),
`worker` (Celery-воркер) і `beat` (Celery-планувальник), на додачу до наявних
`db`/`api`/`front`, у спільній compose-мережі.

- `redis` SHALL зберігати дані в **іменованому Docker volume** і публікувати
  host-порт за схемою `TT-AA-S` — **`11332`** (тип БД `11`, продукт `33`, індекс `2`).
- `worker` і `beat` SHALL використовувати той самий build context, що `api`
  (`./api`), і **не** публікувати портів; обидва залежать від `redis` і `db`.
- `beat` SHALL запускатись рівно в одному екземплярі.

#### Scenario: Compose описує async-стек

- **WHEN** перевіряється `docker-compose.yml`
- **THEN** присутні сервіси `redis`, `worker`, `beat`; `redis` має іменований volume
  і host-порт `11332`; `worker`/`beat` — без публікованих портів і в одній мережі з
  `api`/`db`

#### Scenario: Worker і beat бачать брокер і БД

- **WHEN** піднято `docker compose up`
- **THEN** `worker` і `beat` підключаються до `redis` (`APP__REDIS__URL`) і до `db`,
  а постановлені в чергу задачі виконуються воркером
