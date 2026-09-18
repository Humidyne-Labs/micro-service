# 🔔 webpush-relay (python micro-service)

A lightweight, vendor-agnostic Python micro-service bridging IoT rule engines (such as **ThingsBoard**) with standard W3C Web Push (VAPID) endpoints.

Delivers 24/7 background alerts to Progressive Web Apps (PWAs) and browsers without requiring Firebase SDKs, client-side FCM libraries, or proprietary cloud dependencies.

---

## 🚀 Features

* **Zero Firebase SDKs:** Operates strictly on native browser `pushManager` APIs and standard VAPID credentials ([RFC 8292](https://datatracker.ietf.org/doc/html/rfc8292) / [RFC 8030](https://datatracker.ietf.org/doc/html/rfc8030)).
* **FastAPI + Gunicorn:** High-performance, asynchronous REST backend built with `pywebpush`.
* **ThingsBoard Native:** Seamlessly accepts incoming JSON webhooks from ThingsBoard Rule Chains.
* **Production Containerized:** Multi-arch build pipeline targeting GitHub Container Registry (GHCR).

---

## 🏗️ Architecture

```text
[ ThingsBoard Rule Engine ]
            │
            ▼ (POST /api/v1/notify)
[ webpush-relay (Port 2000) ] ──── Signs VAPID ECDH Payload ────┐
                                                                │
[ PWA Service Worker ] ◄── Hardware Interrupt ◄── [ Google Push Endpoint ]

```

---

## 🛠️ Quick Start

### 1. Environment Configuration

Copy `env.example` to `.env` and populate your VAPID credentials:

```env
VAPID_PUBLIC_KEY=your_public_vapid_key_here
VAPID_PRIVATE_KEY=your_private_vapid_key_here
VAPID_SUBJECT=mailto:email@address.com
PORT=2000

```

### 2. Deploy with Docker Compose

```yaml
version: '3.8'

services:
  webpush-relay:
    image: ghcr.io/humidyne-labs/webpush-relay:latest
    container_name: humid1-webpush-relay
    restart: unless-stopped
    ports:
      - "127.0.0.1:2000:2000"
    env_file:
      - .env

```

Run the container:

```bash
docker compose up -d

```

---

## ⚙️ Environment Variables

| Variable | Description | Default | Required |
| --- | --- | --- | --- |
| `VAPID_PUBLIC_KEY` | Base64 URL-safe VAPID public key exposed to PWA clients | — | **Yes** |
| `VAPID_PRIVATE_KEY` | Base64 URL-safe VAPID private key | — | **Yes** |
| `VAPID_SUBJECT` | Contact URI passed in VAPID headers | `mailto:email@address.com` | No |
| `PORT` | Internal container port | `6000` | No |

---

## 📡 API Reference

All endpoints are available under two equivalent path prefixes:
- `/api/v1/...` — primary
- `/push/api/v1/...` — reverse-proxy alias (e.g. when mounted at a sub-path)

### Get Public VAPID Key

`GET /api/v1/vapid-public-key`

Used by PWA clients to dynamically fetch the server's public key prior to calling `pushManager.subscribe()`. Returns `404` if `VAPID_PUBLIC_KEY` is not configured on the server.

**Response (`200 OK`):**

```json
{
  "public_key": "<your_public_vapid_key_here>"
}

```

---

### Send Push Notification

`POST /api/v1/notify`

**Headers:** `Content-Type: application/json`

**Request Body:**

```json
{
  "subscription": {
    "endpoint": "https://fcm.googleapis.com/fcm/send/...",
    "expirationTime": null,
    "keys": {
      "p256dh": "Blue...",
      "auth": "armadillo..."
    }
  },
  "title": "HUMID1 Alert",
  "body": "Relative Humidity Threshold Breached! Save the Armadillos!",
  "severity": "CRITICAL",
  "deviceId": "abc123",
  "deviceName": "Cabinet Sensor 1",
  "url": "/dashboard",
  "tag": "humidity-alert"
}

```

| Field | Type | Description | Required |
| --- | --- | --- | --- |
| `subscription` | object | W3C Push API subscription object | **Yes** |
| `title` | string | Notification title | **Yes** |
| `body` | string | Notification body text | **Yes** |
| `severity` | string | Alarm severity: `CRITICAL`, `MAJOR`, `MINOR`, `WARNING`, `INFO`, `INDETERMINATE` | No (default: `CRITICAL`) |
| `deviceId` | string | ThingsBoard device ID | No |
| `deviceName` | string | Human-readable device name | No |
| `url` | string | URL to open when the notification is clicked | No (default: `/`) |
| `tag` | string | Notification tag for deduplication | No |

**Response (`200 OK`):**

```json
{
  "status": "delivered",
  "code": 201
}

```

---

### Health Check

`GET /healthz`  
`GET /push/healthz`

**Response (`200 OK`):**

```json
{
  "status": "ok",
  "version": "1.0.8"
}

```

---

### Diagnostics

`GET /api/v1/diagnostics`  
`GET /push/api/v1/diagnostics`

Returns server status, uptime, VAPID configuration state, and running notification metrics.

**Response (`200 OK`):**

```json
{
  "version": "1.0.8",
  "status": "healthy",
  "server_time": "2026-09-18T00:00:00+00:00",
  "uptime_seconds": 3600,
  "config": {
    "vapid_public_key_configured": true,
    "vapid_private_key_configured": true,
    "vapid_subject": "mailto:email@address.com"
  },
  "metrics": {
    "total_notifications_sent": 42,
    "total_errors": 0,
    "last_error": null
  }
}

```

> **Note:** `"status"` is `"healthy"` when `VAPID_PRIVATE_KEY` is set, or `"degraded"` otherwise.

---

## 🔌 ThingsBoard Integration

In your ThingsBoard Rule Chain, add a **REST API Call** node configured as follows:

* **Endpoint URL pattern:** `http://127.0.0.1:2000/api/v1/notify`
* **Request Method:** `POST`
* **Message Payload:**

```json
{
  "subscription": ${ss_push_subscription},
  "title": "HUMID1 Critical Alarm",
  "body": "Cabinet humidity exceeded threshold!"
}

```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.  

## 👥 Contributors

[![none](https://wsrv.nl/?url=github.com/Humiditron.png&w=32&h=32&fit=cover&mask=circle&filt=greyscale "@Humiditron")](https://github.com/Humiditron/)
[![none](https://wsrv.nl/?url=github.com/google-gemini.png&w=32&h=32&fit=cover&mask=circle&filt=greyscale "@google-gemini")](https://github.com/google-gemini/)

© 2026 **Humidyne-Labs**
