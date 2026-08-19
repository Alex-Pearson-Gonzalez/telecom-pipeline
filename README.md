# Telecom Network Data Pipeline

A containerized ETL pipeline that tracks IP address space announcements for major European
telecom operators, using the [RIPEstat API](https://stat.ripe.net/docs/data_api). The pipeline
runs on a schedule, building a historical time series of how each operator's announced network
footprint changes over time.

Built as a hands-on data engineering project alongside a Telecommunications Engineering degree.

---

## What it does

Every hour, the pipeline queries RIPEstat for a set of Autonomous System Numbers (ASNs) belonging
to Spanish telecom operators, counts how many IP prefixes each one currently announces to the
global routing table, and stores a timestamped snapshot in PostgreSQL.

**Operators tracked:**

| ASN | Operator |
|---|---|
| AS3352 | Telefónica de España |
| AS12430 | Vodafone Spain |
| AS12479 | Orange Spain |

Because operators announce and withdraw prefixes continuously, repeated runs produce a genuine
time series rather than a static snapshot.

---

## Architecture

```
                    ┌─────────────────────┐
                    │   RIPEstat API      │
                    │  (public REST API)  │
                    └──────────┬──────────┘
                               │ HTTP GET
                               ▼
┌──────────────────────────────────────────────────────┐
│                 pipeline container                   │
│                                                      │
│   scheduler.py  ──▶  runs pipeline every hour        │
│        │                                             │
│        ▼                                             │
│   pipeline.py   ──▶  orchestration + logging         │
│        │                                             │
│        ├──▶ extract.py    fetch raw JSON             │
│        ├──▶ transform.py  parse + shape the data     │
│        └──▶ load.py       insert via SQLAlchemy ORM  │
│                                                      │
└──────────────────────────┬───────────────────────────┘
                           │ docker network
                           ▼
                ┌──────────────────────┐
                │   postgres container │
                │  network_snapshots   │
                │  (persistent volume) │
                └──────────────────────┘
```

Each ETL stage lives in its own module so failures are easy to isolate: extraction handles
network and API errors, transformation handles data shape, and loading handles database
constraints and transactions.

---

## Tech stack

- **Python 3.12** — pipeline logic
- **PostgreSQL 16** — storage
- **SQLAlchemy 2.0** — ORM layer and session/transaction management
- **requests** — API calls
- **schedule** — in-process job scheduling
- **Docker / Docker Compose** — containerization and orchestration

---

## Running it

**Requirements:** Docker Desktop. Nothing else — no local Python or PostgreSQL install needed.

```bash
git clone https://github.com/Alex-Pearson-Gonzalez/telecom-pipeline.git
cd telecom-pipeline

cp .env.example .env     # then edit .env with your own values

docker compose up --build
```

The pipeline runs once immediately on startup, then repeats hourly. The database schema is
created automatically on first run via `init.sql`.

To inspect the data, connect any PostgreSQL client to `localhost:5433` using the credentials
from your `.env`:

```sql
SELECT * FROM network_snapshots ORDER BY fetched_at DESC;
```

---

## Database schema

```sql
CREATE TABLE network_snapshots (
    id            SERIAL PRIMARY KEY,
    asn           VARCHAR(20)  NOT NULL,
    operator_name VARCHAR(100),
    prefix_count  INTEGER,
    fetched_at    TIMESTAMP    NOT NULL DEFAULT NOW()
);
```

---

## Project structure

```
telecom-pipeline/
├── extract.py           # calls the RIPEstat API, returns raw JSON
├── transform.py         # parses raw JSON into a clean record
├── load.py              # writes records to PostgreSQL via SQLAlchemy
├── pipeline.py          # orchestrates E→T→L, logging, per-ASN error handling
├── scheduler.py         # entry point: runs the pipeline on a schedule
├── models.py            # SQLAlchemy ORM model
├── init.sql             # schema, applied automatically on first DB start
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Design notes

**Per-ASN error isolation.** Each operator is processed inside its own `try/except`. If one API
call fails, the pipeline logs the error, increments a failure counter, and continues with the
next operator rather than aborting the whole run. Each run ends with a success/failure summary.

**Transactional loads.** Every insert runs inside a SQLAlchemy session with explicit
`commit()`/`rollback()`, so a failed write never leaves a partial row behind.

**Configuration via environment.** Connection details come from environment variables rather than
hardcoded strings, so the same code runs unchanged locally and in Docker. The application fails
fast with a clear error if `DATABASE_URL` is missing, rather than silently connecting somewhere
unexpected.

**Persistent storage.** PostgreSQL data lives in a named Docker volume, so snapshots survive
container restarts and the time series keeps accumulating.

**Structured logging.** Logging is configured once at the entry point; every module gets a named
logger and inherits that configuration. Logs go to both stdout and `pipeline.log`, with
timestamps and severity levels.

---

## Possible extensions

- REST API layer (FastAPI) to expose the collected data over HTTP
- Retry logic with exponential backoff for transient API failures
- Deployment to a cloud host with a managed PostgreSQL instance
- Additional RIPEstat endpoints (routing history, geolocation, RPKI validation status)
