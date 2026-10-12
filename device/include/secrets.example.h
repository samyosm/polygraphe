#pragma once

// Copy this file to secrets.h (not committed) and fill it in.

#define WIFI_SSID "my-network"
#define WIFI_PASSWORD "my-password"
// The server's POLYGRAPHE_DEVICE_TOKEN.
#define DEVICE_TOKEN "change-me"

// Optional: override the "overridable" settings of config.h for your own board. For example,
// to send to a backend running on your computer (uv run uvicorn app.main:app --host 0.0.0.0):
// #define SERVER_HOST "192.168.1.20"
// #define SERVER_PORT 8000
// #define SERVER_TLS false
// #define SERVER_BASE_PATH ""
// #define DEVICE_ID "bench-samy"
