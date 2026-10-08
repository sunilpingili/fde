import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from models import Invoice

router = APIRouter()

DATA_FILE = Path(__file__).parent / "data" / "invoices.json"

def load_invoices():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_invoices(invoices):
    with open(DATA_FILE, "w") as f:
        json.dump(invoices, f, indent=4)

@router.post("/invoices")
def create_invoice(invoice: Invoice):
    invoices = load_invoices()
    new_invoice = invoice.model_dump()
    if any(inv["id"] == new_invoice["id"] for inv in invoices):
        raise HTTPException(status_code=409, detail="Invoice with this ID already exists")
    invoices.append(new_invoice)
    save_invoices(invoices)
    return {"message": "Invoice created successfully", "invoice": new_invoice}
