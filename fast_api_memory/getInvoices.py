import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter()

DATA_FILE = Path(__file__).parent / "data" / "invoices.json"

def load_invoices():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

@router.get("/invoices")
def get_invoices():
    return {"invoices": load_invoices()}

@router.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int):
    for invoice in load_invoices():
        if invoice["id"] == invoice_id:
            return {"invoice": invoice}
    raise HTTPException(status_code=404, detail="Invoice not found")