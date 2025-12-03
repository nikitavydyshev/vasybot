from fastapi import FastAPI, Request
import requests
import hashlib
import base64
import json
import config

app = FastAPI()


# ======================================================
# SIGN for Click
# ======================================================
def generate_sign(service_id, merchant_id, transaction_param, amount, secret_key):
    raw = f"{service_id}{merchant_id}{transaction_param}{amount}{secret_key}"
    return hashlib.sha256(raw.encode()).hexdigest()


# ======================================================
# Create Click Invoice
# ======================================================
def create_invoice(user_id: str, amount: int):
    sign = generate_sign(
        config.CLICK_SERVICE_ID,
        config.CLICK_MERCHANT_ID,
        user_id,
        amount,
        config.CLICK_SECRET_KEY
    )

    payload = {
        "service_id": config.CLICK_SERVICE_ID,
        "merchant_id": config.CLICK_MERCHANT_ID,
        "transaction_param": user_id,
        "amount": amount,
        "callback_url": f"{config.DOMAIN}/click",
        "sign": sign
    }

    if config.CLICK_MERCHANT_USER_ID:
        payload["merchant_user_id"] = config.CLICK_MERCHANT_USER_ID

    print("\nCLICK REQUEST:", payload)
    resp = requests.post("https://api.click.uz/v2/invoice/create", json=payload)
    print("CLICK RESPONSE:", resp.text)

    return resp.json()


# ======================================================
# BotHelp Auth
# ======================================================
basic = base64.b64encode(f"{config.BOTHELP_ID}:{config.BOTHELP_SECRET}".encode()).decode()

HEADERS = {
    "Authorization": f"Basic {basic}",
    "Content-Type": "application/json"
}

SEND_URL = "https://main.bothelp.io/botX/sendMessage"


# ======================================================
# Webhook BotHelp
# ======================================================
@app.post("/bothelp")
async def bothelp(request: Request):
    body = await request.json()
    print("\n=== BOTHELP INPUT ===")
    print(json.dumps(body, indent=4, ensure_ascii=False))

    # универсальная обработка webhook
    user_id = body.get("user_id") or body.get("client_id")
    text = body.get("message") or body.get("text") or ""

    if not user_id:
        print("NO USER_ID! Cannot process")
        return {"status": "error", "reason": "no user_id"}

    # обработка кодового слова
    if config.CODE_WORD in text.lower():
        invoice = create_invoice(user_id, config.PAY_AMOUNT)

        if "payment_url" not in invoice:
            return {"error": "no payment_url", "details": invoice}

        message = f"Вот ваша ссылка на оплату:\n{invoice['payment_url']}"

        requests.post(
            SEND_URL,
            headers=HEADERS,
            json={"user_id": user_id, "message": message}
        )

    return {"status": "ok"}


# ======================================================
# Click Callback
# ======================================================
@app.post("/click")
async def click_callback(request: Request):
    data = await request.json()
    print("\nCLICK CALLBACK:", data)

    if data.get("error") == "0" or data.get("status") == "success":
        user_id = data["transaction_param"]

        requests.post(
            SEND_URL,
            headers=HEADERS,
            json={
                "user_id": user_id,
                "message": f"Спасибо за оплату! Вот файл:\n{config.GOOGLE_FILE_URL}"
            }
        )

    return {"status": "received"}
