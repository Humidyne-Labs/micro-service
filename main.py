"""
Module:       main.py
Project:      HUMID1
Author:       Humiditron
Organization: Humidyne Labs
Date:         2026-09-15
License:      MIT

Description:
    Serve encrypted FCM alerts from thingsboard via REST API. 
       - micro-service used in humid1.com server stack.

Dependencies:
    fastapi, pydantic, pywebpush, uvicorn, gunicorn
    Install Note: 'pip install fastapi pydantic pywebpush uvicorn gunicorn'

Usage:
    python main.py
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Literal
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from pywebpush import webpush, WebPushException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webpush-relay")

APP_VERSION = "1.0.6"
START_TIME = datetime.now(timezone.utc)

# Diagnostic telemetry state
diagnostics_state = {
    "total_notifications_sent": 0,
    "total_errors": 0,
    "last_error": None
}

app = FastAPI(title="HUMID1 Web Push Relay", version=APP_VERSION, root_path="/push")

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_SUBJECT = os.getenv("VAPID_SUBJECT", "mailto:email@address.com")


class PushPayload(BaseModel):
    subscription: dict
    title: str
    body: str
    severity: Optional[Literal["CRITICAL", "MAJOR", "MINOR", "WARNING", "INFO", "INDETERMINATE"]] = "CRITICAL"
    deviceId: Optional[str] = ""
    deviceName: Optional[str] = ""
    url: Optional[str] = "/"
    tag: Optional[str] = None


@app.get("/healthz", status_code=status.HTTP_200_OK)
async def health_check():
    return {
        "status": "ok",
        "version": APP_VERSION
    }


@app.get("/api/v1/diagnostics", status_code=status.HTTP_200_OK)
async def get_diagnostics():
    now = datetime.now(timezone.utc)
    uptime_seconds = int((now - START_TIME).total_seconds())

    return {
        "version": APP_VERSION,
        "status": "healthy" if bool(VAPID_PRIVATE_KEY) else "degraded",
        "server_time": now.isoformat(),
        "uptime_seconds": uptime_seconds,
        "config": {
            "vapid_public_key_configured": bool(VAPID_PUBLIC_KEY),
            "vapid_private_key_configured": bool(VAPID_PRIVATE_KEY),
            "vapid_subject": VAPID_SUBJECT,
        },
        "metrics": diagnostics_state
    }


@app.get("/api/v1/vapid-public-key", status_code=status.HTTP_200_OK)
async def get_public_key():
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VAPID_PUBLIC_KEY is not configured on the server."
        )
    return {"public_key": VAPID_PUBLIC_KEY}


@app.post("/api/v1/notify", status_code=status.HTTP_200_OK)
async def send_notification(payload: PushPayload):
    if not VAPID_PRIVATE_KEY:
        logger.error("Attempted to send notification without VAPID_PRIVATE_KEY set.")
        diagnostics_state["total_errors"] += 1
        diagnostics_state["last_error"] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "detail": "VAPID_PRIVATE_KEY missing"
        }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfiguration: VAPID_PRIVATE_KEY missing."
        )

    notification_data = payload.model_dump(exclude={"subscription"}, exclude_none=True)

    try:
        response = webpush(
            subscription_info=payload.subscription,
            data=json.dumps(notification_data),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_SUBJECT},
            ttl=86400
        )
        diagnostics_state["total_notifications_sent"] += 1
        return {"status": "delivered", "code": response.status_code}

    except WebPushException as ex:
        error_body = ex.response.text if ex.response else str(ex)
        logger.error(f"Push delivery failed: {error_body}")
        
        diagnostics_state["total_errors"] += 1
        diagnostics_state["last_error"] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "detail": error_body
        }
        
        raise HTTPException(
            status_code=ex.response.status_code if ex.response else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Push delivery failed: {error_body}"
        )