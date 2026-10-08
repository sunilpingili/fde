from fastapi import FastAPI
from createInvoice import router as create_invoice_router
from getInvoices import router as get_invoice_router
from deleteInvoice import router as delete_invoice_router

app = FastAPI()
app.include_router(create_invoice_router)
app.include_router(get_invoice_router)
app.include_router(delete_invoice_router)
