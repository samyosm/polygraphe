#include "core/Sensor.h"

namespace {
// Constant-initialised, so it is set before any sensor's constructor runs.
Sensor* registered = nullptr;
}  // namespace

Sensor::Sensor(const char* name) : name_(name), next_(registered) { registered = this; }

void Sensor::startAll() {
  if (!registered) LOG("No sensor enabled");
  for (Sensor* s = registered; s; s = s->next_) {
    s->active_ = s->start();
    LOG("Sensor %s: %s", s->name_, s->active_ ? "started" : "FAILED, disabled");
  }
}

void Sensor::loopAll(Reporter& out) {
  for (Sensor* s = registered; s; s = s->next_) {
    if (s->active_) s->loop(out);
  }
}
