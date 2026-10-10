# FDE Practice Repository

A hands-on learning repo for the Testleaf FDE course. Each sub-project has its own folder and a dedicated markdown file documenting what was built and the concepts covered.

**Python version:** 3.13.x (use this across all projects)

---

## Projects

| Project | Folder | Docs | Topics |
|---|---|---|---|
| Invoice API | [fast_api_memory/](fast_api_memory/) | [Invoice_api.md](fast_api_memory/Invoice_api.md) | FastAPI, APIRouter, Pydantic, JSON file persistence |
| PostgreSQL Setup | — | [postgres_setup.md](postgres_setup.md) | PostgreSQL 18, psycopg3, fde_db, .env |
| Public API Practice | [public_api/](public_api/) | — | GET requests, in-memory data |
| Week 1 Setup | [src/](src/) | — | Python basics, FastAPI health endpoint |

> More projects will be added here as the course progresses.

---

## Repo Structure

```text
fde/
├── fast_api_memory/        # Invoice API project
│   ├── main.py
│   ├── createInvoice.py
│   ├── getInvoices.py
│   ├── deleteInvoice.py
│   ├── models.py
│   ├── data/invoices.json  # excluded from git
│   └── Invoice_api.md
├── public_api/             # Public API practice
├── src/                    # Week 1 basics
├── data/                   # Sample CSV files
├── requirements.txt
└── .gitignore
```

---

## Setup

### 1. Clone the repo

```sh
git clone https://github.com/sunilpingili/fde.git
cd fde
```

### 2. Create and activate virtual environment

**macOS:**
```sh
python3.13 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```sh
pip install -r requirements.txt
```

---

## Running a project

Each project has its own `uvicorn` command. Example for the Invoice API:

```sh
cd fast_api_memory
uvicorn main:app --reload --port 8001
```

Then open [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs) for the interactive Swagger UI.

---

## Tools used

- [FastAPI](https://fastapi.tiangolo.com/) — API framework
- [Pydantic](https://docs.pydantic.dev/) — data validation
- [Uvicorn](https://www.uvicorn.org/) — ASGI server
- [LangChain / LangGraph](https://www.langchain.com/) — AI/agent workflows (upcoming projects)
- [pre-commit](https://pre-commit.com/) + [detect-secrets](https://github.com/Yelp/detect-secrets) — code quality and secret scanning
