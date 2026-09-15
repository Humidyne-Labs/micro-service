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
[ webpush-relay (Port 6000) ] ──── Signs VAPID ECDH Payload ────┐
                                                                │
[ PWA Service Worker ] ◄── Hardware Interrupt ◄── [ Google Push Endpoint ]

```

---

## 🛠️ Quick Start

### 1. Environment Configuration

Copy `.env.example` to `.env` and populate your VAPID credentials:

```env
VAPID_PUBLIC_KEY=your_public_vapid_key_here
VAPID_PRIVATE_KEY=your_private_vapid_key_here
VAPID_SUBJECT=mailto:email@address.com
PORT=6000

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
      - "127.0.0.1:6000:6000"
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
| `VAPID_PUBLIC_KEY` | Base64 URL-safe VAPID public key exposed to PWA clients | — | No |
| `VAPID_PRIVATE_KEY` | Base64 URL-safe VAPID private key | — | **Yes** |
| `VAPID_SUBJECT` | Contact URI passed in VAPID headers | `mailto:email@address.com` | No |
| `PORT` | Internal container port | `6000` | No |

---

## 📡 API Reference

### Get Public VAPID Key

`GET /api/v1/vapid-public-key`

Used by PWA clients to dynamically fetch the server's public key prior to calling `pushManager.subscribe()`.

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
    "endpoint": "[https://fcm.googleapis.com/fcm/send/](https://fcm.googleapis.com/fcm/send/)...",
    "expirationTime": null,
    "keys": {
      "p256dh": "Blue...",
      "auth": "armadillo..."
    }
  },
  "title": "HUMID1 Alert",
  "body": "Relative Humidity Threshold Breached! Save the Armadillos!"
}

```

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

**Response (`200 OK`):**

```json
{
  "status": "ok"
}

```

---

## 🔌 ThingsBoard Integration

In your ThingsBoard Rule Chain, add a **REST API Call** node configured as follows:

* **Endpoint URL pattern:** `http://127.0.0.1:6000/api/v1/notify`
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
