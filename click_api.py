import requests
import hashlib
import time
import config
from datetime import datetime

def make_auth_header():
    """
    CLICK Auth header: merchant_user_id : sha1(timestamp + secret_key) : timestamp
    """
    timestamp = str(int(time.time()))
    digest_raw = timestamp + config.CLICK_SECRET_KEY
    digest = hashlib.sha1(digest_raw.encode()).hexdigest()

    auth_header = f"{config.CLICK_MERCHANT_USER_ID}:{digest}:{timestamp}"

    return {
        "Auth": auth_header,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def check_payment_status_by_mti(mti: str, time: str):
    
    """
    Проверка оплаты по MTI (transaction_param)
    Использует CLICK endpoint:
    GET /v2/merchant/payment/status/:service_id/:merchant_trans_id
    """
    url = (
        f"https://api.click.uz/v2/merchant/payment/status_by_mti/"
        f"{config.CLICK_SERVICE_ID}/{mti}/{time}"
    )

    headers = make_auth_header()

    print("\n===== CHECK PAYMENT REQUEST =====")
    print("URL:", url)
    print("HEADERS:", headers)
    print("=================================")

    try:
        response = requests.get(url, headers=headers)
        print("CLICK RESPONSE:", response.text)
        print("=================================\n")

        return response.json()

    except Exception as e:
        return {"error": "request_failed", "details": str(e)}
