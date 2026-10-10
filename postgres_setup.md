# PostgreSQL 18 Setup — macOS

Week 2 Day 4 setup for PostgreSQL + FastAPI using Postgres.app on macOS.

---

## Classroom Settings

| Setting   | Value          |
|-----------|----------------|
| Host      | localhost      |
| Port      | 5432           |
| Database  | fde_db         |
| User      | fde_user       |
| Password  | FDE_Local_2026 |
| Python DB | Psycopg 3      |

---

## Installation

Installed via **Postgres.app** (not EDB installer).

Download: [postgresapp.com](https://postgresapp.com)

Select PostgreSQL 18 when prompted.

---

## Add psql to PATH

Add this line to `~/.zshrc`:

```sh
export PATH="/Applications/Postgres.app/Contents/Versions/18/bin:$PATH"
```

Then reload:

```sh
source ~/.zshrc
```

Verify:

```sh
psql --version
# Expected: psql (PostgreSQL) 18.x
```

---

## Starting Postgres

Postgres.app runs from the **menu bar** (elephant icon, top right).

- Click the elephant → **Open Postgres** to see the GUI
- Click **Start** if not already running
- To auto-start on login: **Server Settings** → check **Automatically start server on login**

---

## Connect via Terminal

```sh
psql -U sunil -h localhost -p 5432
```

Verify version:

```sql
SELECT version();
```

Exit:

```sh
\q
```

---

## Database Setup

Run these commands to create the classroom database, user, and table.

### Create user and database

```sql
CREATE USER fde_user WITH PASSWORD 'FDE_Local_2026';
CREATE DATABASE fde_db OWNER fde_user;
```

### Create invoices table

```sql
\c fde_db

CREATE TABLE IF NOT EXISTS invoices (
    id     SERIAL PRIMARY KEY,
    amount NUMERIC(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL
);
```

### Insert sample rows

```sql
INSERT INTO invoices (amount, status) VALUES
    (100.00, 'paid'),
    (200.00, 'unpaid'),
    (300.00, 'unpaid'),
    (400.00, 'paid'),
    (500.00, 'unpaid'),
    (600.00, 'paid');
```

### Grant permissions

```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fde_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fde_user;
```

---

## Python Setup

### Install packages

```sh
pip install "psycopg[binary]" python-dotenv
```

### .env file

Create a `.env` file in the project root:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fde_db
DB_USER=fde_user
DB_PASSWORD=FDE_Local_2026
```

> `.env` is in `.gitignore` — never commit it.

### Test connection

```python
import psycopg

conn = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="fde_db",
    user="fde_user",
    password="FDE_Local_2026"
)
cur = conn.cursor()
cur.execute("SELECT * FROM invoices;")
rows = cur.fetchall()
for row in rows:
    print(row)
conn.close()
```

Expected output:

```
(1, Decimal('100.00'), 'paid')
(2, Decimal('200.00'), 'unpaid')
(3, Decimal('300.00'), 'unpaid')
(4, Decimal('400.00'), 'paid')
(5, Decimal('500.00'), 'unpaid')
(6, Decimal('600.00'), 'paid')
```

---

## Ready-for-Class Checklist

- [x] PostgreSQL 18 installed
- [x] Server running on port 5432
- [x] pgAdmin / Postgres.app GUI available
- [x] `psql --version` works
- [x] `localhost:5432` reachable
- [x] `fde_user` exists
- [x] `fde_db` exists
- [x] `invoices` table exists
- [x] Sample rows exist
- [x] Virtual environment works
- [x] Psycopg 3 installed and imports
- [x] `.env` exists
- [x] Python connection succeeds
