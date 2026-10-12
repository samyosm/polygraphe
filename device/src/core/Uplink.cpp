#include "core/Uplink.h"

#include "core/Log.h"
#include "platform/Platform.h"

namespace {

void logMeasurement(const Measurement& m) {
  String line = m.type();
  for (uint8_t i = 0; i < m.fieldCount(); ++i) {
    const Measurement::Field& f = m.field(i);
    line += ' ';
    line += f.name;
    line += '=';
    switch (f.kind) {
      case Measurement::Field::Kind::Number: line += String(f.number, 3); break;
      case Measurement::Field::Kind::Integer: line += String(static_cast<long>(f.integer)); break;
      case Measurement::Field::Kind::Boolean: line += f.boolean ? "true" : "false"; break;
    }
  }
  LOG("%s", line.c_str());
}

}  // namespace

void Uplink::begin() {
  deviceId_ = strlen(DEVICE_ID) > 0 ? String(DEVICE_ID) : "polygraphe-" + platform::chipId();
  path_ = String(SERVER_BASE_PATH) + "/ws/devices/" + deviceId_;
  authorization_ = String("Authorization: Bearer ") + DEVICE_TOKEN;
  LOG("Device %s, server %s://%s:%d%s", deviceId_.c_str(), SERVER_TLS ? "wss" : "ws", SERVER_HOST,
      SERVER_PORT, path_.c_str());

  LOG("WiFi: connecting to %s", WIFI_SSID);
  platform::wifiBegin(WIFI_SSID, WIFI_PASSWORD, deviceId_.c_str());
  platform::startClock(NTP_SERVER);

  socket_.onEvent([this](WStype_t type, uint8_t* payload, size_t length) {
    onEvent(type, payload, length);
  });
  socket_.setExtraHeaders(authorization_.c_str());
  socket_.setReconnectInterval(UPLINK_RECONNECT_INTERVAL_MS);
  // Detects dead connections (e.g. the server restarted) within about 30 s.
  socket_.enableHeartbeat(15000, 5000, 2);
  // No subprotocol: the server does not use any.
  if (SERVER_TLS) {
    socket_.beginSSL(SERVER_HOST, SERVER_PORT, path_.c_str(), nullptr, "");
  } else {
    socket_.begin(SERVER_HOST, SERVER_PORT, path_.c_str(), "");
  }
}

void Uplink::loop() {
  const bool wifi = platform::wifiConnected();
  if (wifi != wifiConnected_) {
    wifiConnected_ = wifi;
    if (wifi) {
      LOG("WiFi: connected, IP %s", platform::localIp().c_str());
    } else {
      LOG("WiFi: disconnected");
    }
  }
  if (!wifi) return;

  socket_.loop();
  if (flushTimer_.due()) flush();
}

void Uplink::send(const Measurement& m) {
  if (LOG_MEASUREMENTS) logMeasurement(m);
  if (!socket_.isConnected()) {
    ++dropped_;
    return;
  }

  JsonObject message = batch_.add<JsonObject>();
  message["type"] = m.type();
  JsonObject fields = message["fields"].to<JsonObject>();
  for (uint8_t i = 0; i < m.fieldCount(); ++i) {
    const Measurement::Field& f = m.field(i);
    switch (f.kind) {
      case Measurement::Field::Kind::Number: fields[f.name] = f.number; break;
      case Measurement::Field::Kind::Integer: fields[f.name] = f.integer; break;
      case Measurement::Field::Kind::Boolean: fields[f.name] = f.boolean; break;
    }
  }
  if (m.tagCount() > 0) {
    JsonObject tags = message["tags"].to<JsonObject>();
    for (uint8_t i = 0; i < m.tagCount(); ++i) tags[m.tag(i).key] = m.tag(i).value;
  }
  // Without a clock, the server uses the arrival time instead.
  const uint64_t timestamp = m.timestamp() ? m.timestamp() : platform::epochMillis();
  if (timestamp) message["timestamp"] = timestamp;

  if (batch_.size() >= UPLINK_MAX_BATCH) flush();
}

void Uplink::flush() {
  if (batch_.size() == 0) return;
  String frame;
  serializeJson(batch_, frame);
  batch_.clear();
  if (!socket_.sendTXT(frame)) LOG("Server: failed to send %u bytes", frame.length());
}

void Uplink::onEvent(WStype_t type, uint8_t* payload, size_t length) {
  switch (type) {
    case WStype_CONNECTED:
      LOG("Server: connected");
      if (dropped_ > 0) {
        LOG("Server: %lu measurements dropped while disconnected", static_cast<unsigned long>(dropped_));
        dropped_ = 0;
      }
      break;
    case WStype_DISCONNECTED:
      // Also reported for every failed attempt, e.g. a wrong DEVICE_TOKEN (refused handshake).
      LOG("Server: disconnected, retrying in %d ms", UPLINK_RECONNECT_INTERVAL_MS);
      batch_.clear();
      break;
    case WStype_TEXT: {
      // The server only talks to report invalid frames: {"status": "error", "detail": ...}.
      JsonDocument reply;
      if (deserializeJson(reply, payload, length) == DeserializationError::Ok &&
          reply["status"] == "error") {
        LOG("Server rejected a frame: %s", reply["detail"].as<const char*>());
      }
      break;
    }
    case WStype_ERROR:
      LOG("Server: error %.*s", static_cast<int>(length), reinterpret_cast<char*>(payload));
      break;
    default:
      break;
  }
}
