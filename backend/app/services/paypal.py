import time, base64
import httpx
from app.core.config import CLIENT_ID, SECRET, BASE

_token = None
_token_expiry = 0

async def get_access_token():
    global _token, _token_expiry
    if _token and time.time() < _token_expiry - 60:
        return _token
    url = f"{BASE}/v1/oauth2/token"
    auth = httpx.BasicAuth(CLIENT_ID, SECRET)
    async with httpx.AsyncClient() as client:
        r = await client.post(url, auth=auth, data={"grant_type":"client_credentials"})
    r.raise_for_status()
    d = r.json()
    _token = d["access_token"]
    _token_expiry = time.time() + d.get("expires_in", 3600)
    return _token

async def create_order(amount: str, currency: str = "USD"):
    token = await get_access_token()
    url = f"{BASE}/v2/checkout/orders"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"intent":"CAPTURE","purchase_units":[{"amount":{"currency_code":currency,"value":amount}}]}
    async with httpx.AsyncClient() as client:
        r = await client.post(url, json=body, headers=headers)
    r.raise_for_status()
    return r.json()

async def capture_order(order_id: str):
    token = await get_access_token()
    url = f"{BASE}/v2/checkout/orders/{order_id}/capture"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        r = await client.post(url, headers=headers)
    r.raise_for_status()
    return r.json()

async def verify_webhook_signature(transmission_id, transmission_time, cert_url, auth_algo, transmission_sig, webhook_event):
    token = await get_access_token()
    url = f"{BASE}/v1/notifications/verify-webhook-signature"
    payload = {
        "transmission_id": transmission_id,
        "transmission_time": transmission_time,
        "cert_url": cert_url,
        "auth_algo": auth_algo,
        "transmission_sig": transmission_sig,
        "webhook_id": None,   # put your WEBHOOK_ID from dashboard if you have it
        "webhook_event": webhook_event
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type":"application/json"}
    async with httpx.AsyncClient() as client:
        r = await client.post(url, json=payload, headers=headers)
    r.raise_for_status()
    return r.json()
