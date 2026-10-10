# Invoice API

A simple FastAPI project that manages invoices. Data is stored in a JSON file so it persists across server restarts.

---

## Project Structure

```
fast_api_memory/
├── main.py               # App entry point, registers all routers
├── getInvoices.py        # GET endpoints
├── createInvoice.py      # POST endpoint
├── deleteInvoice.py      # DELETE endpoint
├── models.py             # Pydantic model for Invoice
├── data_store.py         # (legacy) in-memory list, no longer used
└── data/
    └── invoices.json     # Persistent storage
```

---

## Invoice Model

Defined in `models.py` using Pydantic. Every invoice must have these fields:

| Field    | Type    | Example       |
|----------|---------|---------------|
| `id`     | str     | `"7"`         |
| `amount` | float   | `1000.0`      |
| `status` | str     | `"paid"`      |

---

## API Endpoints

| Method   | Endpoint                | Description              |
|----------|-------------------------|--------------------------|
| `GET`    | `/invoices`             | Get all invoices         |
| `GET`    | `/invoices/{invoice_id}`| Get one invoice by ID    |
| `POST`   | `/invoices`             | Create a new invoice     |
| `DELETE` | `/invoices/{invoice_id}`| Delete an invoice by ID  |

---

## How Data Persistence Works

Every file uses the same two helpers to read and write `invoices.json`:

```python
def load_invoices():
    with open(DATA_FILE, "r") as f:
        return json.load(f)       # JSON file → Python list

def save_invoices(invoices):
    with open(DATA_FILE, "w") as f:
        json.dump(invoices, f, indent=4)  # Python list → JSON file
```

---

## Flowcharts

### GET /invoices
```
Client
  │
  ▼
GET /invoices
  │
  ▼
load_invoices()
  │  reads data/invoices.json
  ▼
Return full list → 200 OK
```

---

### POST /invoices
```
Client sends JSON body
{ "id": "7", "amount": 700, "status": "unpaid" }
  │
  ▼
Pydantic validates against Invoice model
  │
  ├── invalid? → 422 Unprocessable Entity
  │
  ▼
load_invoices()   ← read current list from JSON
  │
  ▼
invoices.append(new_invoice)   ← add to list in RAM
  │
  ▼
save_invoices()   ← write updated list back to JSON
  │
  ▼
Return { "message": "Invoice created", "invoice": {...} } → 200 OK
```

---

### DELETE /invoices/{invoice_id}
```
Client
  │
  ▼
DELETE /invoices/3
  │
  ▼
load_invoices()   ← read current list from JSON
  │
  ▼
Loop through list looking for id == 3
  │
  ├── not found? → raise HTTPException → 404 Not Found
  │
  ▼
invoices.pop(i)   ← remove from list in RAM
  │
  ▼
save_invoices()   ← write updated list back to JSON
  │
  ▼
Return { "message": "Invoice deleted", "invoice": {...} } → 200 OK
```

---

## Running the Server

```bash
cd fast_api_memory
uvicorn main:app --reload --port 8001
```

Then open [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs) to try the API interactively via FastAPI's built-in Swagger UI.

---

## Key Concepts Learned

| Concept | What it does |
|---|---|
| `APIRouter` | Splits routes across multiple files instead of one big `main.py` |
| `app.include_router()` | Registers a router's routes into the main app |
| `Pydantic BaseModel` | Validates and parses incoming JSON request bodies automatically |
| `HTTPException` | Returns proper HTTP error status codes (e.g. 404) instead of always 200 |
| `json.load()` | Reads a JSON file into a Python list/dict |
| `json.dump()` | Writes a Python list/dict back to a JSON file |
| `Path(__file__).parent` | Resolves file paths relative to the current file, not the working directory |
