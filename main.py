from fastapi import FastAPI, Request
import time
import config
from click_api import check_payment_status_by_mti

app = FastAPI()


@app.post("/create_invoice")
async def create_invoice(request: Request):
    """
    Получаем user_id и amount от BotHelp
    Генерируем ссылку на оплату (Simple Checkout)
    """
    data = await request.json()
    print("🔥 CREATE INVOICE DATA:", data)

    user_id = str(data.get("bothelp_user_id") or data.get("user_id"))
    amount = int(data.get("amount", config.GUIDE_PRICE))

    if not user_id:
        return {"error": "missing_user_id"}

    timestamp = int(time.time())

    transaction_param = f"{user_id}-{timestamp}"

    payment_link = (
        f"https://my.click.uz/services/pay?"
        f"service_id={config.CLICK_SERVICE_ID}"
        f"&merchant_id={config.CLICK_MERCHANT_ID}"
        f"&amount={amount}"
        f"&transaction_param={transaction_param}"
    )

    return {
        "status": "ok",
        "payment_link": payment_link,
        "mti": transaction_param,
    }


@app.get("/check_payment")
async def check_payment(mti: str):
    """
    Проверка оплаты по MTI (transaction_param)
    """
    print("🔍 CHECK PAYMENT MTI:", mti)

    result = check_payment_status_by_mti(mti)

    # Успешные статусы
    if (
        result.get("payment_status") == 1
        or result.get("transaction_state") == 2
        or (result.get("status") or "").lower() == "confirmed"
        or "успешно" in (result.get("error_note") or "").lower()
    ):
        return {"status": "paid"}

    return {"status": "not_paid", "details": result}
