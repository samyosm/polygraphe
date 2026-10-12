// The clock works the same way on the ESP8266 and the ESP32 (newlib + SNTP).
#if defined(ESP8266) || defined(ESP32)

#include <sys/time.h>
#include <time.h>

#include "platform/Platform.h"

namespace platform {

void startClock(const char* ntpServer) { configTime(0, 0, ntpServer); }

uint64_t epochMillis() {
  timeval now;
  gettimeofday(&now, nullptr);
  // Before the first NTP answer, the clock starts at 1970.
  if (now.tv_sec < 1600000000) return 0;
  return static_cast<uint64_t>(now.tv_sec) * 1000 + now.tv_usec / 1000;
}

}  // namespace platform

#endif
