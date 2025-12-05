import time
from fastapi import FastAPI
from click_api import create_invoice, check_invoice_status

app = FastAPI()

@app.post("/create_invoice")
def create_invoice_endpoint(data: dict):
    print("🔥 /create_invoice CALLED")
    print("DATA:", data)

    user_id = data.get("bothelp_user_id")
    amount = data.get("amount")

    if not user_id or not amount:
        return {"error": "missing_parameters"}

    transaction_param = f"{user_id}-{int(time.time())}"

    result = create_invoice(amount, transaction_param)

    return result


@app.get("/check_payment")
def check_payment(invoice_id: str):
    print("🔥 /check_payment CALLED")
    result = check_invoice_status(invoice_id)
    return result
