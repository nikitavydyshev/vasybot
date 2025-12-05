import hashlib
import time
import requests
from config import (
    CLICK_MERCHANT_ID,
    CLICK_SERVICE_ID,
    CLICK_MERCHANT_USER_ID,
    CLICK_SECRET_KEY,
    CLICK_BASE_URL
)

def make_auth_headers():
    timestamp = str(int(time.time()))

    raw = timestamp + CLICK_SECRET_KEY
    digest = hashlib.sha1(raw.encode()).hexdigest()

    auth = f"{CLICK_MERCHANT_USER_ID}:{digest}:{timestamp}"

    print("\n===== AUTH DEBUG =====")
    print("timestamp:", timestamp)
    print("digest_raw:", raw)
    print("digest:", digest)
    print("auth header:", auth)
    print("======================\n")

    return {
        "Auth": auth,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }


def create_invoice(amount, transaction_param):
    url = f"{CLICK_BASE_URL}/v2/merchant/invoice/create/"

    payload = {
        "service_id": CLICK_SERVICE_ID,
        "merchant_id": CLICK_MERCHANT_ID,
        "amount": amount,
        "transaction_param": transaction_param
    }

    headers = make_auth_headers()

    print("\n===== CREATE INVOICE DEBUG =====")
    print("URL:", url)
    print("PAYLOAD:", payload)
    print("HEADERS:", headers)

    response = requests.post(url, json=payload, headers=headers)
    print("CLICK RESPONSE:", response.text)
    print("=================================\n")

    try:
        return response.json()
    except:
        return {"error": "click_invalid_json", "raw": response.text}


def check_invoice_status(invoice_id):
    url = f"{CLICK_BASE_URL}/v2/merchant/invoice/status/{CLICK_SERVICE_ID}/{invoice_id}"

    headers = make_auth_headers()

    print("\n===== CHECK STATUS DEBUG =====")
    print("URL:", url)
    print("HEADERS:", headers)

    response = requests.get(url, headers=headers)
    print("CLICK RESPONSE:", response.text)
    print("=================================\n")

    try:
        return response.json()
    except:
        return {"error": "click_invalid_json", "raw": response.text}
