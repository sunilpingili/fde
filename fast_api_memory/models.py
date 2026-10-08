from pydantic import BaseModel

class Invoice(BaseModel):
    id: str
    amount: float
    status: str