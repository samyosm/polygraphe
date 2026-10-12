#if defined(ESP32)

#include <WiFi.h>

#include "config.h"
#include "platform/Platform.h"

namespace platform {

const char* name() { return "ESP32"; }

void begin() {
  // Do not write the WiFi credentials to flash on every boot.
  WiFi.persistent(false);
}

String chipId() { return String(static_cast<uint32_t>(ESP.getEfuseMac() >> 16), HEX); }

void wifiBegin(const char* ssid, const char* password, const char* hostname) {
  WiFi.setHostname(hostname);  // Must come before the WiFi starts.
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(ssid, password);
}

bool wifiConnected() { return WiFi.status() == WL_CONNECTED; }

String localIp() { return WiFi.localIP().toString(); }

uint32_t readMillivolts(uint8_t pin) {
  // Calibrated by the core, 0 to about 3.1 V with the default attenuation.
  return analogReadMilliVolts(pin);
}

}  // namespace platform

#endif
