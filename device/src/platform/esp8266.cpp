#if defined(ESP8266)

#include <ESP8266WiFi.h>

#include "config.h"
#include "platform/Platform.h"

namespace platform {

const char* name() { return "ESP8266"; }

void begin() {
  // Do not write the WiFi credentials to flash on every boot.
  WiFi.persistent(false);
}

String chipId() { return String(ESP.getChipId(), HEX); }

void wifiBegin(const char* ssid, const char* password, const char* hostname) {
  WiFi.mode(WIFI_STA);
  WiFi.hostname(hostname);
  WiFi.setAutoReconnect(true);
  WiFi.begin(ssid, password);
}

bool wifiConnected() { return WiFi.status() == WL_CONNECTED; }

String localIp() { return WiFi.localIP().toString(); }

uint32_t readMillivolts(uint8_t pin) {
  // A0 is the only analog input: 10 bits over ESP8266_ADC_FULL_SCALE_MV.
  return static_cast<uint32_t>(analogRead(pin)) * ESP8266_ADC_FULL_SCALE_MV / 1023;
}

}  // namespace platform

#endif
