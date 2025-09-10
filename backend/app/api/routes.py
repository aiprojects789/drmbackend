from fastapi import APIRouter, Request, Header, HTTPException
from pydantic import BaseModel
from app.services.paypal import create_order, capture_order, verify_webhook_signature

router = APIRouter()

class CreateOrderReq(BaseModel):
    amount: str
    currency: str = "USD"

@router.post("/create-order")
async def create_order_endpoint(req: CreateOrderReq):
    # IMPORTANT: validate amount on server side; don't trust client
    order = await create_order(req.amount, req.currency)
    return order

@router.post("/capture-order/{order_id}")
async def capture_order_endpoint(order_id: str):
    capture = await capture_order(order_id)
    return capture

@router.post("/webhook")
async def webhook_listener(request: Request,
                           paypal_transmission_id: str = Header(None),
                           paypal_transmission_time: str = Header(None),
                           paypal_cert_url: str = Header(None),
                           paypal_auth_algo: str = Header(None),
                           paypal_transmission_sig: str = Header(None)):
    body = await request.json()
    # Optionally verify with PayPal
    verify_resp = await verify_webhook_signature(paypal_transmission_id, paypal_transmission_time, paypal_cert_url, paypal_auth_algo, paypal_transmission_sig, body)
    if verify_resp.get("verification_status") != "SUCCESS":
        raise HTTPException(status_code=400, detail="Webhook verification failed")
    # handle events (PAYMENT.CAPTURE.COMPLETED etc.)
    return {"status":"ok"}
