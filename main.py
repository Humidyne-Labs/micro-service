import os
import json
import logging
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from pywebpush import webpush, WebPushException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webpush-relay")

app = FastAPI(title="HUMID1 Web Push Relay", version="1.0.0")

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_SUBJECT = os.getenv("VAPID_SUBJECT", "mailto:email@address.com")

class PushPayload(BaseModel):
    subscription: dict
    title: str
    body: str
    
@app.get("/healthz", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}
    
@app.get("/api/v1/vapid-public-key")
async def get_public_key():
    return {"public_key": VAPID_PUBLIC_KEY}        

@app.post("/api/v1/notify", status_code=status.HTTP_200_OK)
async def send_notification(payload: PushPayload):
    if not VAPID_PRIVATE_KEY:
        logger.error("Attempted to send notification without VAPID_PRIVATE_KEY set.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfiguration: VAPID_PRIVATE_KEY missing."
        )

    try:
        response = webpush(
            subscription_info=payload.subscription,
            data=json.dumps({
                "title": payload.title,
                "body": payload.body
            }),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_SUBJECT},
            ttl=86400
        )
        return {"status": "delivered", "code": response.status_code}
    except WebPushException as ex:
        error_body = ex.response.text if ex.response else str(ex)
        logger.error(f"Push delivery failed: {error_body}")
        raise HTTPException(
            status_code=ex.response.status_code if ex.response else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Push delivery failed: {error_body}"
        )
        