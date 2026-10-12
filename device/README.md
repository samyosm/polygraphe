# PolyGraphe — device

Firmware of the measuring device: reads the sensors and streams their measurements over WiFi
to the processing server (see "Device protocol" in [`backend/README.md`](../backend/README.md)).
Built with [PlatformIO](https://platformio.org), for the ESP8266 (NodeMCU) and the ESP32.

## Getting started

1. In VS Code, install the **PlatformIO IDE** extension and open the `device/` folder (not the
   repository root) so PlatformIO finds `platformio.ini`.
2. `cp include/secrets.example.h include/secrets.h` and fill in the WiFi network and the
   server's `POLYGRAPHE_DEVICE_TOKEN`. `secrets.h` is not committed.
3. Plug the board in, then **Upload** and **Monitor** from the PlatformIO toolbar, or:

```bash
pio run -e esp8266 -t upload   # -e esp32 for an ESP32
pio device monitor
```

The board then shows up in the interface as `polygraphe-<chip id>` (or `DEVICE_ID`, if set).

**From WSL**, the USB port must first be handed over to Linux. In an administrator PowerShell
on Windows: `usbipd list`, then `usbipd bind --busid <id>` (once) and
`usbipd attach --wsl --busid <id>` (after each replug). The board appears as `/dev/ttyUSB0`;
your user must be in the group that owns it (`ls -l /dev/ttyUSB0`, usually `dialout` or `uucp`).

**Against a local backend**, override the server in `secrets.h` (see the example in
`secrets.example.h`) and start uvicorn with `--host 0.0.0.0`. A backend inside WSL is not
reachable from the network by default: enable WSL's mirrored networking, or run it on Windows.

## Layout

| Path | |
| --- | --- |
| `include/config.h` | **Every setting**: pins, sample rates, calibration, server, WiFi timings. |
| `include/secrets.h` | WiFi credentials and device token (from `secrets.example.h`). Can override the server for your own board. |
| `src/sensors/` | **One file per sensor**, each with its own `start()` and `loop()`. |
| `src/core/` | What sensors build on: `Sensor`, `Measurement`, `Every` (timer), and `Uplink`, which sends the data. |
| `src/platform/` | Everything specific to a microcontroller (WiFi, ADC, chip id, clock), one file per microcontroller. |
| `src/main.cpp` | Starts the uplink and the sensors, then runs their loops. Nothing sensor-specific. |

## Sensors

### GSR — Grove GSR v1.2 (`src/sensors/gsr.cpp`)

Sends `gsr` measurements at 10 Hz: `conductance` (µS), `resistance` (Ω) and `voltage` (mV).

| Module | ESP8266 (NodeMCU) | ESP32 |
| --- | --- | --- |
| VCC | 3V3 | 3V3 |
| GND | GND | GND |
| SIG | A0 | GPIO 34 |

Power it from **3.3 V**: its output follows its supply, and 5 V would exceed what the ADC accepts.

**Calibration**: set `LOG_MEASUREMENTS 1` in `config.h`, upload, and watch the monitor without
touching the electrodes. Turn the potentiometer on the module until `voltage` reads about half
the supply (1650 mV), then put the value you actually read in `GSR_CALIBRATION_MV`.
`conductance` and `resistance` are left out whenever the voltage is above that value.

## Adding a sensor

Create `src/sensors/<name>.cpp`; nothing else has to change, so several people can work on
different sensors without touching each other's files. Put its pins and settings in `config.h`:

```cpp
#include "config.h"

#if BREATHING_ENABLED

#include "core/Sensor.h"

namespace {

class BreathingSensor : public Sensor {
 public:
  BreathingSensor() : Sensor("breathing") {}

  // Once, at boot. Return false if the sensor is missing: it is then left out.
  bool start() override {
    pinMode(BREATHING_PIN, INPUT);
    return true;
  }

  // Called continuously: return quickly, never use delay().
  void loop(Reporter& out) override {
    if (!sampling_.due()) return;
    out.send(Measurement("breathing").set("value", platform::readMillivolts(BREATHING_PIN)));
  }

 private:
  Every sampling_{BREATHING_SAMPLE_INTERVAL_MS};
};

REGISTER_SENSOR(BreathingSensor);

}  // namespace

#endif
```

- The measurement type (`"breathing"`) is what the server stores and the interface charts; any
  name works, unknown ones are stored too. Reuse the server's names where they exist
  (`heart_rate`, `spo2`, `breathing_rate`, `sweat`, `gsr`; see `backend/app/domain/kinds.py`).
- Use `platform::` functions rather than chip-specific APIs, so the sensor works on every board.
  Libraries for I²C/SPI sensors go in `lib_deps` in `platformio.ini`.
- `LOG(...)` prints to the serial monitor; `LOG_MEASUREMENTS 1` prints everything sent.

## Supporting another microcontroller

1. Add an environment to `platformio.ini` (`[env:<name>]` with its `platform` and `board`).
2. Implement the functions of `src/platform/Platform.h` in `src/platform/<name>.cpp`, wrapped in
   `#if defined(<its macro>)`, and allow that macro at the top of `Platform.h`.
3. Give every sensor a pin for it in `config.h`.

The websocket library (`links2004/WebSockets`) supports ESP8266, ESP32 and RP2040 (Pico W);
for anything else `core/Uplink.cpp` would need another one.

## Notes

- Measurements are timestamped on the board once its clock is set over NTP (a few seconds after
  connecting), and by the server on arrival before that. They are sent in batches every 250 ms;
  those made while disconnected are dropped.
- The TLS connection to the server is encrypted but the certificate is not checked.
- A wrong `DEVICE_TOKEN` shows up as `Server: disconnected` repeating every 5 seconds.
