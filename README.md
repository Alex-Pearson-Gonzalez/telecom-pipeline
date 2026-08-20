# Telecom Network Data Pipeline

A containerized ETL pipeline that tracks IP address space announcements for major European
telecom operators, using the [RIPEstat API](https://stat.ripe.net/docs/data_api). The pipeline
runs on a schedule, building a historical time series of how each operator's announced network
footprint changes over time.

Deployed on **AWS** (ECS Fargate + RDS PostgreSQL) and **Railway**, from the same container image.

Built as a hands-on data engineering project alongside a Telecommunications Engineering degree.

---

## What it does

Every hour, the pipeline queries RIPEstat for a set of Autonomous System Numbers (ASNs) belonging
to Spanish telecom operators, counts how many IP prefixes each one currently announces to the
global routing table, and stores a timestamped snapshot in PostgreSQL.

**Operators tracked:**

| ASN | Operator | Typical prefix count |
|---|---|---|
| AS3352 | Telefónica de España | ~228 |
| AS12430 | Vodafone Spain | ~47 |
| AS12479 | Orange Spain | ~8,560 |

The spread between operators is itself interesting: Orange announces thousands of small,
fragmented prefixes (mostly `/24`s), while Telefónica announces far fewer but much larger blocks
(mostly `/16`s). A higher prefix count means more separate announcements, not more IP space.

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
│        │             creates schema on startup       │
│        ▼                                             │
│   pipeline.py   ──▶  orchestration + logging         │
│        │                                             │
│        ├──▶ extract.py    fetch raw JSON             │
│        ├──▶ transform.py  parse + shape the data     │
│        └──▶ load.py       insert via SQLAlchemy ORM  │
│                                                      │
└──────────────────────────┬───────────────────────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │   PostgreSQL         │
                │  network_snapshots   │
                └──────────────────────┘
```

Each ETL stage lives in its own module so failures are easy to isolate: extraction handles
network and API errors, transformation handles data shape, and loading handles database
constraints and transactions.

---

## Tech stack

- **Python 3.12** — pipeline logic
- **PostgreSQL** — storage
- **SQLAlchemy 2.0** — ORM layer, session and transaction management, schema generation
- **requests** — API calls
- **schedule** — in-process job scheduling
- **Docker / Docker Compose** — containerization and local orchestration
- **AWS** — ECS Fargate (compute), ECR (image registry), RDS (managed PostgreSQL), CloudWatch (logs)
- **Railway** — alternative managed deployment

---

## Running it locally

**Requirements:** Docker Desktop. Nothing else — no local Python or PostgreSQL install needed.

```bash
git clone https://github.com/Alex-Pearson-Gonzalez/telecom-pipeline.git
cd telecom-pipeline

cp .env.example .env     # then edit .env with your own values

docker compose up --build
```

The pipeline runs once immediately on startup, then repeats hourly. The database schema is
created automatically from the SQLAlchemy models on first run.

To inspect the data, connect any PostgreSQL client to `localhost:5433` using the credentials
from your `.env`:

```sql
SELECT * FROM network_snapshots ORDER BY fetched_at DESC;
```

---

## Cloud deployment

The same image runs unchanged on both platforms — the only difference is where `DATABASE_URL`
points. That portability is the point of reading configuration from the environment.

### AWS (ECS Fargate + RDS)

```
Local Docker image
      │  docker push
      ▼
   Amazon ECR  ──────▶  ECS Fargate task
   (registry)           (runs the container)
                              │
                              ▼
                     RDS PostgreSQL
                     (managed database)
```

1. Image built locally and pushed to a private **ECR** repository.
2. An **ECS task definition** specifies the image, CPU/memory (0.25 vCPU / 0.5 GB), and injects
   `DATABASE_URL` as an environment variable.
3. An **ECS service** on Fargate keeps one task running continuously, with a public IP so the
   container can reach the RIPEstat API.
4. **RDS** provides the managed PostgreSQL instance.
5. Logs stream to **CloudWatch**.

### Railway

Deployed directly from this GitHub repository — Railway detects the `Dockerfile` and rebuilds on
every push to `main`. A managed PostgreSQL service supplies `DATABASE_URL` via a reference
variable, so the connection string is never hardcoded.

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

Generated automatically at runtime from the SQLAlchemy models via `Base.metadata.create_all()`,
so a fresh database needs no manual setup on any platform.

---

## Project structure

```
telecom-pipeline/
├── extract.py           # calls the RIPEstat API, returns raw JSON
├── transform.py         # parses raw JSON into a clean record
├── load.py              # writes records to PostgreSQL via SQLAlchemy
├── pipeline.py          # orchestrates E→T→L, logging, per-ASN error handling
├── scheduler.py         # entry point: creates schema, runs pipeline on a schedule
├── models.py            # SQLAlchemy ORM models
├── init.sql             # schema for local docker-compose runs
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
This was validated in practice — when the container initially couldn't reach the database, all
three operators failed cleanly and the scheduler kept running rather than crashing.

**Transactional loads.** Every insert runs inside a SQLAlchemy session with explicit
`commit()`/`rollback()`, so a failed write never leaves a partial row behind.

**Configuration via environment.** Connection details come from environment variables rather than
hardcoded strings, which is what makes the same image portable across local Docker, Railway, and
AWS. The application fails fast with a clear error if `DATABASE_URL` is missing, rather than
silently connecting somewhere unexpected.

**Schema as code.** Tables are generated from the SQLAlchemy models rather than a manually applied
SQL file, so the models are the single source of truth and any fresh database self-initializes.

**Structured logging.** Logging is configured once at the entry point; every module gets a named
logger and inherits that configuration. Logs go to stdout, picked up by CloudWatch on AWS and by
Railway's log viewer, with timestamps and severity levels.

---

## Notes on the AWS deployment

Getting the container to reach RDS required an inbound rule on the database's security group
allowing PostgreSQL traffic from the ECS task's security group — referencing the security group
rather than an IP address, since Fargate tasks receive a new IP on every restart. The failure
mode was a connection timeout, which at first glance is indistinguishable from an unreachable
host, and is worth knowing as a common AWS networking issue.

For a production deployment, two things here would change: `DATABASE_URL` would live in AWS
Secrets Manager rather than as a plaintext environment variable in the task definition, and the
RDS instance would not have public access enabled — it is enabled here only so the database can
be inspected directly during development.

---

## Possible extensions

- REST API layer (FastAPI) to expose the collected data over HTTP
- Retry logic with exponential backoff for transient API failures
- Secrets Manager integration for database credentials
- Additional RIPEstat endpoints (routing history, geolocation, RPKI validation status)
