#pragma once

#include <Arduino.h>

// One sample sent to the server: a type (e.g. "gsr") and one or more named values.
//
//   out.send(Measurement("gsr").set("conductance", 3.1f).set("voltage", 912));
//
// Names must be string literals (they are not copied) made of [A-Za-z0-9_.-]. Timestamps are
// added when the measurement is sent; call at() only to date it otherwise.
class Measurement {
 public:
  static constexpr uint8_t kMaxFields = 8;
  static constexpr uint8_t kMaxTags = 4;

  struct Field {
    enum class Kind : uint8_t { Number, Integer, Boolean };
    const char* name;
    Kind kind;
    union {
      double number;
      long long integer;
      bool boolean;
    };
  };

  struct Tag {
    const char* key;
    const char* value;
  };

  explicit Measurement(const char* type) : type_(type) {}

  Measurement& set(const char* name, double value);
  Measurement& set(const char* name, float value) { return set(name, static_cast<double>(value)); }
  Measurement& set(const char* name, bool value);
  Measurement& set(const char* name, int value) { return setInteger(name, value); }
  Measurement& set(const char* name, long value) { return setInteger(name, value); }
  Measurement& set(const char* name, long long value) { return setInteger(name, value); }
  Measurement& set(const char* name, unsigned value) { return setInteger(name, value); }
  Measurement& set(const char* name, unsigned long value) { return setInteger(name, value); }

  // String metadata, e.g. tag("sensor", "grove_gsr_v1.2").
  Measurement& tag(const char* key, const char* value);

  // Unix time in milliseconds.
  Measurement& at(uint64_t epochMillis) {
    timestamp_ = epochMillis;
    return *this;
  }

  const char* type() const { return type_; }
  uint8_t fieldCount() const { return fieldCount_; }
  const Field& field(uint8_t i) const { return fields_[i]; }
  uint8_t tagCount() const { return tagCount_; }
  const Tag& tag(uint8_t i) const { return tags_[i]; }
  uint64_t timestamp() const { return timestamp_; }  // 0 if not set.

 private:
  Measurement& setInteger(const char* name, long long value);
  Field* add(const char* name, Field::Kind kind);

  const char* type_;
  Field fields_[kMaxFields];
  uint8_t fieldCount_ = 0;
  Tag tags_[kMaxTags];
  uint8_t tagCount_ = 0;
  uint64_t timestamp_ = 0;
};
