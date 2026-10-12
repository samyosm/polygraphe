#pragma once

#include <Arduino.h>

// Everything that differs from one microcontroller to another. Each supported microcontroller
// implements these functions in its own file of this folder (esp8266.cpp, esp32.cpp), compiled
// only for it; the rest of the firmware only uses this interface.
//
// Supporting a new microcontroller: add a [env:...] to platformio.ini, a <board>.cpp here, and
// its pins in config.h.

#if !defined(ESP8266) && !defined(ESP32)
#error "Unsupported microcontroller: implement src/platform/Platform.h for it."
#endif

namespace platform {

// Short name of the microcontroller, for logs.
const char* name();

// Called first thing in setup().
void begin();

// Unique identifier of this chip, as hexadecimal.
String chipId();

// Starts connecting to the WiFi network, and reconnects by itself whenever it is lost.
void wifiBegin(const char* ssid, const char* password, const char* hostname);
bool wifiConnected();
String localIp();

// Voltage on an analog pin, in millivolts.
uint32_t readMillivolts(uint8_t pin);

// Starts synchronising the clock over NTP, in the background.
void startClock(const char* ntpServer);
// Current time as Unix milliseconds, or 0 while the clock is not set yet.
uint64_t epochMillis();

}  // namespace platform
