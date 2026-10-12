#pragma once

#include <Arduino.h>

// Non-blocking timer for loop() functions:
//
//   Every sampling{100};
//   void loop(Reporter& out) { if (!sampling.due()) return; ... }
//
// due() is true once per period, the first time right away. It keeps a steady rate, but skips
// the missed periods instead of catching up when the loop was blocked for a while.
class Every {
 public:
  explicit Every(uint32_t periodMs) : period_(periodMs) {}

  bool due() {
    const uint32_t now = millis();
    if (started_ && now - last_ < period_) return false;
    last_ = started_ && now - last_ < 2 * period_ ? last_ + period_ : now;
    started_ = true;
    return true;
  }

 private:
  uint32_t period_;
  uint32_t last_ = 0;
  bool started_ = false;
};
