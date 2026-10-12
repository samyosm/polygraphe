#pragma once

#include <Arduino.h>
#include <ArduinoJson.h>
#include <WebSocketsClient.h>

#include "config.h"
#include "core/Every.h"
#include "core/Reporter.h"

// Sends measurements to the processing server over a websocket (see "Device protocol" in
// backend/README.md), grouped in small batches. Keeps the WiFi and the connection up, and
// reconnects by itself. Measurements made while disconnected are dropped.
class Uplink : public Reporter {
 public:
  void begin();
  void loop();
  void send(const Measurement& measurement) override;

 private:
  void flush();
  void onEvent(WStype_t type, uint8_t* payload, size_t length);

  WebSocketsClient socket_;
  JsonDocument batch_;
  String deviceId_;
  String path_;
  String authorization_;
  bool wifiConnected_ = false;
  uint32_t dropped_ = 0;
  Every flushTimer_{UPLINK_FLUSH_INTERVAL_MS};
};
