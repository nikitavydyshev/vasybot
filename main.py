from fastapi import FastAPI, Request
import requests
import hashlib
import base64

# Загружаем конфиг
import config

app = FastAPI()


# ======================================================
# Генерация подписи Click
# ======================================================
def generate_sign(service_id, merchant_id, transaction_param, amount, secret_key):
    raw = f"{service_id}{merchant_id}{transaction_param}{amount}{secret_key}"
    return hashlib.sha256(raw.encode()).hexdigest()


# ======================================================
# Создание инвойса Click
# ======================================================
def create_click_invoice(user_id: str, amount: int):
    transaction_param = user_id

    sign = generate_sign(
        config.CLICK_SERVICE_ID,
        config.CLICK_MERCHANT_ID,
        transaction_param,
        amount,
        config.CLICK_SECRET_KEY
    )

    payload = {
        "service_id": config.CLICK_SERVICE_ID,
        "merchant_id": config.CLICK_MERCHANT_ID,
        "transaction_param": transaction_param,
        "amount": amount,
        "callback_url": f"{config.DOMAIN}/click",
        "sign": sign
    }

    if config.CLICK_MERCHANT_USER_ID:
        payload["merchant_user_id"] = config.CLICK_MERCHANT_USER_ID

    resp = requests.post("https://api.click.uz/v2/invoice/create", json=payload)
    data = resp.json()

    print("CLICK RESPONSE:", data)
    return data


# ======================================================
# Подготовка BotHelp авторизации
# ======================================================
basic_token = base64.b64encode(
    f"{config.BOTHELP_ID}:{config.BOTHELP_SECRET}".encode()
).decode()

BOTHELP_HEADERS = {
    "Authorization": f"Basic {basic_token}",
    "Content-Type": "application/json"
}

BOTHELP_SEND_URL = "https://main.bothelp.io/botX/sendMessage"


# ======================================================
# Обработка сообщений BotHelp
# ======================================================
@app.post("/bothelp")
async def bothelp_webhook(request: Request):
    body = await request.json()
    print("BOTHELP INPUT:", body)

    user_id = body["from"]["id"]
    text = body.get("text", "").lower()

    if config.CODE_WORD in text:
        invoice = create_click_invoice(user_id, config.PAY_AMOUNT)

        if "payment_url" not in invoice:
            print("CLICK ERROR:", invoice)
            return {"error": "click_failed", "details": invoice}

        requests.post(
            BOTHELP_SEND_URL,
            headers=BOTHELP_HEADERS,
            json={
                "user_id": user_id,
                "message": f"Вот ваша ссылка на оплату:\n{invoice['payment_url']}"
            }
        )

    return {"status": "ok"}


# ======================================================
# Обработка callback Click
# ======================================================
@app.post("/click")
async def click_callback(request: Request):
    data = await request.json()
    print("CLICK CALLBACK:", data)

    # успешный платеж
    if data.get("error") == "0" or data.get("status") == "success":
        user_id = data["transaction_param"]

        requests.post(
            BOTHELP_SEND_URL,
            headers=BOTHELP_HEADERS,
            json={
                "user_id": user_id,
                "message": f"Оплата прошла успешно! Вот ваш файл:\n{config.GOOGLE_FILE_URL}"
            }
        )

    return {"status": "received"}
