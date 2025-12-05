from fastapi import FastAPI, Request
import requests
import hashlib
import time

from config import (
    CLICK_SERVICE_ID,
    CLICK_MERCHANT_ID,
    CLICK_MERCHANT_USER_ID,
    CLICK_SECRET_KEY,
    CLICK_BASE_URL
)

app = FastAPI()


def make_auth_header():
    timestamp = str(int(time.time()))
    digest_raw = timestamp + CLICK_SECRET_KEY
    digest = hashlib.sha1(digest_raw.encode()).hexdigest()

    auth_value = f"{CLICK_MERCHANT_USER_ID}:{digest}:{timestamp}"

    return {"Auth": auth_value}


@app.post("/create_invoice")
async def create_invoice(request: Request):
    body = await request.json()

    user_id = body.get("user_id")
    amount = body.get("amount")

    if not user_id or not amount:
        return {"error": "Missing user_id or amount"}

    url = f"{CLICK_BASE_URL}/v2/merchant/invoice/create"

    payload = {
        "service_id": CLICK_SERVICE_ID,
        "merchant_id": CLICK_MERCHANT_ID,
        "amount": amount,
        "transaction_param": user_id
    }

    headers = make_auth_header()

    print("\n📤 CREATE INVOICE → CLICK")
    print("Headers:", headers)
    print("Payload:", payload)

    try:
        response = requests.post(url, json=payload, headers=headers)
        print("📥 CLICK RESPONSE:", response.text)
        data = response.json()
    except Exception as e:
        print("❌ Ошибка CLICK:", e)
        return {"error": "click_error"}

    # CLICK success?
    invoice_id = data.get("invoice_id")
    payment_url = data.get("payment_url")

    if not invoice_id:
        return {"error": "invoice_create_failed", "details": data}

    return {
        "invoice_id": invoice_id,
        "payment_url": payment_url
    }


@app.get("/check_invoice")
def check_invoice(invoice_id: int):

    url = f"{CLICK_BASE_URL}/v2/merchant/invoice/status/{CLICK_SERVICE_ID}/{invoice_id}"

    headers = make_auth_header()

    print("\n🔎 CHECK INVOICE STATUS → CLICK")
    print("Headers:", headers)

    try:
        response = requests.get(url, headers=headers)
        print("📥 CLICK RESPONSE:", response.text)
        data = response.json()
    except Exception as e:
        print("❌ Ошибка CLICK:", e)
        return {"paid": False}

    status = data.get("invoice_status")

    if status == 2:
        return {"paid": True}

    return {"paid": False}
