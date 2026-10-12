#pragma once

// Every setting of the device: pins, timings, WiFi and server. Secrets (WiFi password, device
// token) live in secrets.h, which is not committed: copy secrets.example.h to secrets.h.
// secrets.h is read first, so it can also override any setting below marked "overridable",
// e.g. to point your own board at a server running on your computer.

#if __has_include("secrets.h")
#include "secrets.h"
#else
#error "Missing include/secrets.h: copy include/secrets.example.h to include/secrets.h and fill it in."
#endif

#if !defined(WIFI_SSID) || !defined(WIFI_PASSWORD) || !defined(DEVICE_TOKEN)
#error "include/secrets.h must define WIFI_SSID, WIFI_PASSWORD and DEVICE_TOKEN."
#endif

// ---------------------------------------------------------------------------------------------
// General
// ---------------------------------------------------------------------------------------------

#define SERIAL_BAUD 115200

// Print logs on the serial port.
#define LOG_ENABLED 1
// Also print every measurement on the serial port (handy when working on a sensor).
#define LOG_MEASUREMENTS 0

// ---------------------------------------------------------------------------------------------
// Identity and server (overridable)
// ---------------------------------------------------------------------------------------------

// Name of the device on the server ([A-Za-z0-9_-], at most 64 characters). Empty: derived from
// the chip id, e.g. "polygraphe-a1b2c3", so every board gets its own.
#ifndef DEVICE_ID
#define DEVICE_ID ""
#endif

// The device connects to ws(s)://SERVER_HOST:SERVER_PORT SERVER_BASE_PATH/ws/devices/<DEVICE_ID>.
#ifndef SERVER_HOST
#define SERVER_HOST "polygraphe.samy.dev"
#endif
#ifndef SERVER_PORT
#define SERVER_PORT 443
#endif
// Encrypted connection (wss://). The server certificate is not verified.
#ifndef SERVER_TLS
#define SERVER_TLS true
#endif
// "/api" behind the deployment proxy, "" when talking to uvicorn directly.
#ifndef SERVER_BASE_PATH
#define SERVER_BASE_PATH "/api"
#endif

// Used to timestamp measurements. Until the clock is set, the server timestamps them on arrival.
#ifndef NTP_SERVER
#define NTP_SERVER "pool.ntp.org"
#endif

// ---------------------------------------------------------------------------------------------
// Uplink
// ---------------------------------------------------------------------------------------------

// Measurements are grouped and sent at most this often...
#define UPLINK_FLUSH_INTERVAL_MS 250
// ...or as soon as this many are waiting.
#define UPLINK_MAX_BATCH 32
// Delay between two connection attempts to the server.
#define UPLINK_RECONNECT_INTERVAL_MS 5000

// ---------------------------------------------------------------------------------------------
// Board
// ---------------------------------------------------------------------------------------------

#if defined(ESP8266)
// Voltage read on A0 at full scale. NodeMCU and Wemos D1 mini boards have a divider that brings
// it to about 3.2 V; on a bare ESP-12 module it is 1.0 V.
#define ESP8266_ADC_FULL_SCALE_MV 3200
#endif

// ---------------------------------------------------------------------------------------------
// Sensors: GSR (Grove GSR v1.2), see src/sensors/gsr.cpp
// ---------------------------------------------------------------------------------------------

#define GSR_ENABLED 1

// SIG pin of the module. Power the module from 3.3 V, never 5 V: its output follows its supply.
#if defined(ESP8266)
#define GSR_PIN A0
#elif defined(ESP32)
#define GSR_PIN 34  // ADC1 only: ADC2 pins cannot be read while WiFi is on.
#endif

#define GSR_SAMPLE_INTERVAL_MS 100  // 10 Hz: skin conductance changes slowly.
#define GSR_OVERSAMPLING 8          // Readings averaged into each sample.
#define GSR_SUPPLY_MV 3300          // Supply voltage of the module.
// Output voltage with nobody touching the electrodes. Turn the module's potentiometer so that it
// reads about half the supply, then write the value you measure here (see device/README.md).
#define GSR_CALIBRATION_MV 1650
