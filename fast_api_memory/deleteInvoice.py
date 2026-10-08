import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter()

DATA_FILE = Path(__file__).parent / "data" / "invoices.json"

def load_invoices():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_invoices(invoices):
    with open(DATA_FILE, "w") as f:
        json.dump(invoices, f, indent=4)

@router.delete("/invoices/{invoice_id}")
def delete_invoice(invoice_id: str):
    invoices = load_invoices()
    for i, invoice in enumerate(invoices):
        if invoice["id"] == invoice_id:
            deleted_invoice = invoices.pop(i)
            save_invoices(invoices)
            return {"message": "Invoice deleted successfully", "invoice": deleted_invoice}
    raise HTTPException(status_code=404, detail="Invoice not found")