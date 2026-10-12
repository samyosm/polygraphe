// Galvanic skin response (sweat), with a Grove GSR v1.2 module.
//
// The module outputs a voltage that drops as the skin between the two electrodes conducts more.
// Sends "gsr" measurements with:
//   conductance  skin conductance, in µS (missing when the reading is out of range)
//   resistance   skin resistance, in Ω (idem)
//   voltage      module output, in mV
// Settings: GSR_* in config.h.

#include "config.h"

#if GSR_ENABLED

#include "core/Sensor.h"

namespace {

class GsrSensor : public Sensor {
 public:
  GsrSensor() : Sensor("gsr") {}

  bool start() override {
    LOG("GSR on pin %d: %lu mV (no contact should read about %d mV)", GSR_PIN,
        static_cast<unsigned long>(readMillivolts()), GSR_CALIBRATION_MV);
    return true;
  }

  void loop(Reporter& out) override {
    if (!sampling_.due()) return;

    const float mv = readMillivolts();
    Measurement m("gsr");
    // Seeed's formula R = (1024 + 2x) * 10000 / (512 - x), with x the 10-bit reading at
    // supply voltage and 512 the reading without contact, rewritten with voltages.
    if (mv < GSR_CALIBRATION_MV) {
      const float ohms = 10000.0f * (GSR_SUPPLY_MV + 2 * mv) / (GSR_CALIBRATION_MV - mv);
      m.set("conductance", 1e6f / ohms).set("resistance", ohms);
    }
    m.set("voltage", mv).tag("sensor", "grove_gsr_v1.2");
    out.send(m);
  }

 private:
  static float readMillivolts() {
    uint32_t sum = 0;
    for (int i = 0; i < GSR_OVERSAMPLING; ++i) sum += platform::readMillivolts(GSR_PIN);
    return static_cast<float>(sum) / GSR_OVERSAMPLING;
  }

  Every sampling_{GSR_SAMPLE_INTERVAL_MS};
};

REGISTER_SENSOR(GsrSensor);

}  // namespace

#endif
