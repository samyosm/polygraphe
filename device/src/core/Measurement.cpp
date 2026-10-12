#include "core/Measurement.h"

#include "core/Log.h"

Measurement& Measurement::set(const char* name, double value) {
  if (Field* f = add(name, Field::Kind::Number)) f->number = value;
  return *this;
}

Measurement& Measurement::set(const char* name, bool value) {
  if (Field* f = add(name, Field::Kind::Boolean)) f->boolean = value;
  return *this;
}

Measurement& Measurement::setInteger(const char* name, long long value) {
  if (Field* f = add(name, Field::Kind::Integer)) f->integer = value;
  return *this;
}

Measurement& Measurement::tag(const char* key, const char* value) {
  if (tagCount_ == kMaxTags) {
    LOG("%s: too many tags, '%s' ignored", type_, key);
    return *this;
  }
  tags_[tagCount_++] = {key, value};
  return *this;
}

Measurement::Field* Measurement::add(const char* name, Field::Kind kind) {
  if (fieldCount_ == kMaxFields) {
    LOG("%s: too many fields, '%s' ignored", type_, name);
    return nullptr;
  }
  Field& f = fields_[fieldCount_++];
  f.name = name;
  f.kind = kind;
  return &f;
}
