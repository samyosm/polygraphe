#pragma once

#include <Arduino.h>

#include "config.h"
#include "core/Every.h"
#include "core/Log.h"
#include "core/Measurement.h"
#include "core/Reporter.h"
#include "platform/Platform.h"

// A sensor of the device. Each one lives in its own file of src/sensors/ and registers itself
// with REGISTER_SENSOR, so adding a sensor never means editing a shared file (besides its
// settings in config.h). See src/sensors/gsr.cpp.
class Sensor {
 public:
  explicit Sensor(const char* name);
  virtual ~Sensor() = default;

  const char* name() const { return name_; }

  // Called once from setup(). Return false if the sensor cannot work (e.g. not wired): it is
  // then left out and its loop() is never called.
  virtual bool start() = 0;

  // Called on every pass of the main loop, so it must return quickly: no delay(), use Every
  // to run at a given rate.
  virtual void loop(Reporter& out) = 0;

  // Used by main.cpp.
  static void startAll();
  static void loopAll(Reporter& out);

 private:
  const char* name_;
  bool active_ = false;
  Sensor* next_;
};

// Creates the single instance of a sensor class, which registers it.
#define REGISTER_SENSOR(Type) static Type Type##Instance
