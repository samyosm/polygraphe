// PolyGraphe device: reads the sensors of src/sensors/ and streams their measurements to the
// processing server. Nothing sensor-specific happens here.

#include <Arduino.h>

#include "config.h"
#include "core/Log.h"
#include "core/Sensor.h"
#include "core/Uplink.h"
#include "platform/Platform.h"

namespace {
Uplink uplink;
}  // namespace

void setup() {
  Serial.begin(SERIAL_BAUD);
  platform::begin();
  LOG("PolyGraphe device on %s", platform::name());
  uplink.begin();
  Sensor::startAll();
}

void loop() {
  uplink.loop();
  Sensor::loopAll(uplink);
}
