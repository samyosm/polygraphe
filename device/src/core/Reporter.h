#pragma once

#include "core/Measurement.h"

// Where sensors send their measurements. Sensors only know this interface, not how (or whether)
// the data leaves the board.
class Reporter {
 public:
  virtual ~Reporter() = default;
  virtual void send(const Measurement& measurement) = 0;
};
