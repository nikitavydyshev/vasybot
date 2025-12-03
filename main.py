from fastapi import FastAPI, Request
import requests
import hashlib
import base64
import json
import config  # импорт конфигураций

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

    # merchant_user_id нужен не во всех сервисах
    if config.CLICK_MERCHANT_USER_ID:
        payload["merchant_user_id"] = config.CLICK_MERCHANT_USER_ID

    print("\n=== CLICK REQUEST PAYLOAD ===")
    print(json.dumps(payload, indent=4, ensure_ascii=False))

    resp = requests.post("https://api.click.uz/v2/invoice/create", json=payload)
    data = resp.json()

    print("\n=== CLICK RESPONSE ===")
    print(json.dumps(data, indent=4, ensure_ascii=False))

    return data


# ======================================================
# Подготовка авторизации BotHelp
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
# Вебхук от BotHelp
# ======================================================
@app.post("/bothelp")
async def bothelp_webhook(request: Request):
    body = await request.json()

    print("\n\n======================= BOTHELP INPUT =======================")
    print(json.dumps(body, indent=4, ensure_ascii=False))

    # гарантированно проверяем наличие ключей
    user_id = body.get("client_id")
    text = body.get("text", "")

    if not user_id:
        print("❌ ERROR: BotHelp не передал client_id")
        return {"error": "no_client_id"}

    text_lower = text.lower()

    # если пользователь написал кодовое слово
    if config.CODE_WORD in text_lower:
        invoice = create_click_invoice(user_id, config.PAY_AMOUNT)

        if "payment_url" not in invoice:
            print("❌ ERROR: Click не выдал payment_url")
            return {"error": "click_failed", "details": invoice}

        # отправляем ссылку пользователю
        message = f"Отлично! Вот ваша ссылка на оплату:\n{invoice['payment_url']}"

        print("\n=== BOTHELP SEND MESSAGE (payment link) ===")
        print(message)

        requests.post(
            BOTHELP_SEND_URL,
            headers=BOTHELP_HEADERS,
            json={"user_id": user_id, "message": message}
        )

    return {"status": "ok"}


# ======================================================
# Вебхук Click (оплата)
# ======================================================
@app.post("/click")
async def click_callback(request: Request):
    data = await request.json()

    print("\n\n======================= CLICK CALLBACK =======================")
    print(json.dumps(data, indent=4, ensure_ascii=False))

    # Проверяем успешность
    if data.get("error") == "0" or data.get("status") == "success":
        user_id = data["transaction_param"]

        message = f"Спасибо за оплату! Вот ваш файл:\n{config.GOOGLE_FILE_URL}"

        print("\n=== BOTHELP SEND MESSAGE (file delivery) ===")
        print(message)

        requests.post(
            BOTHELP_SEND_URL,
            headers=BOTHELP_HEADERS,
            json={"user_id": user_id, "message": message}
        )

    else:
        print("❌ CLICK CALLBACK ERROR:", data)

    return {"status": "received"}
