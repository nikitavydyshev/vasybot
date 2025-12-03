from fastapi import FastAPI, Request
import requests

app = FastAPI()

# ------------------------------------
# CONFIG — ВСТАВЛЯЕШЬ СВОИ ДАННЫЕ
# ------------------------------------
CLICK_SERVICE_ID = "87456"
CLICK_MERCHANT_ID = "50415"

BOTHELP_CLIENT_ID = "574704:e1a97fcf5deeffe1ea80909096a6178d"
BOTHELP_CLIENT_SECRET = "574704:39fdd14df52f1e5eed9d983d310f1cc4"

FILE_URL = "https://drive.google.com/drive/folders/1XJNg1A8fJCjkUOyoDobndS9HumV023yb"

SERVER_URL = "<<< URL_ТВОЕГО_СЕРВЕРА >>>"  # без слэша в конце
# ------------------------------------


# 1) WEBHOOK ОТ BOTHELP
@app.post("/bothelp")
async def bothelp_webhook(data: dict):
    client_id = data["client_id"]

    # создаём инвойс CLICK
    invoice = requests.post(
        "https://api.click.uz/v2/invoice/create",
        json={
            "service_id": CLICK_SERVICE_ID,
            "merchant_id": CLICK_MERCHANT_ID,
            "amount": 1000,
            "transaction_param": f"user_{client_id}",
            "callback_url": f"{SERVER_URL}/click_callback",
            "return_url": "https://google.com"
        }
    ).json()

    # возвращаем BotHelp текст + кнопку
    return {
        "message": "Прекрасно! Вот ваша ссылка на оплату:",
        "buttons": [
            {
                "text": "Оплатить",
                "url": invoice["payment_url"]
            }
        ]
    }


# 2) CALLBACK ОТ CLICK
@app.post("/click_callback")
async def click_callback(request: Request):
    data = await request.json()

    # click присылает transaction_param = "user_517461"
    client_id = data["transaction_param"].replace("user_", "")

    # получаем токен bothelp
    token = requests.post(
        "https://oauth.bothelp.io/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": BOTHELP_CLIENT_ID,
            "client_secret": BOTHELP_CLIENT_SECRET
        }
    ).json()["access_token"]

    # отправляем сообщение клиенту через BotHelp API
    requests.post(
        "https://api.bothelp.io/v1/messages",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "client_id": client_id,
            "type": "text",
            "message": f"Спасибо за оплату! Вот ваш файл:\n{FILE_URL}"
        }
    )

    return {"status": "ok"}
