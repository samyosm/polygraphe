#pragma once

#include <Arduino.h>

#include "config.h"

// printf-style log line on the serial port, prefixed with the uptime in milliseconds.
#define LOG(fmt, ...)                                                                \
  do {                                                                               \
    if (LOG_ENABLED) Serial.printf("[%9lu] " fmt "\n", millis(), ##__VA_ARGS__); \
  } while (0)
