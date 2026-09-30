# PolyGraphe — processing server

Receives measurements from the device over a websocket, stores them **raw** in InfluxDB right
away, then runs processors that derive new data from them (also stored in InfluxDB). It also
manages *trials* (stored in SQLite) and serves everything to the interface, live included.

## Running

```bash
cp .env.example .env
docker compose up -d                  # InfluxDB on :8086 (UI: admin / polygraphe-admin)
uv run uvicorn app.main:app --reload  # server on :8000
```

With no database at all (data lost on restart): `POLYGRAPHE_STORAGE_BACKEND=memory uv run uvicorn app.main:app`.

Checks: `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`

## Architecture

```
 DataSource ──stream()──▶ IngestionService ──write(RAW)──▶ PublishingRepository ──▶ Influx / InMemory
 (WebSocket, Dummy)                                          │ ▲
                                                   publish() │ │ write(PROCESSED)
                                                             ▼ │
                                   MeasurementBus ──▶ ProcessingEngine ── Processor: fetch → process → store
                                                 └──▶ TrialService.live() ──▶ /trials/{id}/live (interface)
```

| Package | Role |
| --- | --- |
| `app/domain` | `Measurement` (kind, device, fields, timestamp, tags), `Stage` (raw/processed), `Trial` and its life cycle. No dependencies. |
| `app/storage/measurements` | `MeasurementRepository` interface: `InfluxRepository`, `InMemoryRepository`, and `PublishingRepository`, a decorator that announces every write on the bus. |
| `app/storage/trials` | `TrialRepository` interface: `SqlTrialRepository` (SQLAlchemy, SQLite by default) and `InMemoryTrialRepository`. |
| `app/bus.py` | `MeasurementBus`: in-process publish/subscribe of stored measurements. |
| `app/ingestion` | `DataSource` interface (`WebSocketSource`, `DummySource`), `IngestionService` (stores raw data) and `DeviceRegistry` (connected devices). |
| `app/processing` | `Processor` interface, `ProcessingEngine` (scheduling) and the concrete processors. |
| `app/trials` | `TrialService`: trial use cases, the measurements of a trial, its live feed. |
| `app/api` | FastAPI routes and their schemas, kept apart from the domain. |
| `app/services.py` | Composition root, the only place that picks concrete classes. |

Dependencies only point inwards: `domain` imports nothing, `storage` only knows `domain`, and so on.
Changing a database means writing a new repository, with nothing else to touch.

## Trials

A trial goes `created → recording ⇄ paused → completed`. Each recording period is a *segment*
(device + start/stop), so a trial's data is simply "what its device sent during its segments":
the device never needs to know about trials. A device can only be recorded by one trial at a time.

| Endpoint | |
| --- | --- |
| `GET /trials?q=` | List, newest first. `q` searches titles and subject names. |
| `POST /trials` | Create: `{"title", "description"?, "subject"?: {"name", "age", "sex", "culture"}}`. |
| `GET /trials/{id}` | One trial, with its segments. |
| `PUT /trials/{id}` | Replace its details (title, description, subject). Allowed in any status, even saved. |
| `POST /trials/{id}/start` | Start or resume data intake: `{"device_id"}`. |
| `POST /trials/{id}/stop` | Stop intake, can be resumed. |
| `POST /trials/{id}/complete` | Stop intake for good (save). |
| `GET /trials/{id}/measurements?since=` | Raw and processed measurements of the trial. |
| `WS /trials/{id}/live?since=` | Measurements since `since`, then live ones while recording. |
| `WS /trials/events` | Every trial, each time it changes (creation, edit, status). |
| `GET /devices` | Devices currently connected. |

Watching is open to everyone. Everything that changes a trial (`POST`/`PUT` above) needs an
operator session: `POST /auth/operator {"password"}` returns a token, sent as
`Authorization: Bearer <token>`. Tokens are stateless and signed (`app/auth.py`), and they expire after
`POLYGRAPHE_OPERATOR_SESSION_HOURS`. The password is `POLYGRAPHE_OPERATOR_PASSWORD` (`dummy` by default).

Invalid transitions and busy devices answer `409`, unknown trials `404`. Interactive docs are at
`/docs`; the interface generates its TypeScript types from `/openapi.json`.

## Device protocol

Connect to `ws://<server>:8000/ws/devices/<device_id>?token=<POLYGRAPHE_DEVICE_TOKEN>` (or send
the token as an `Authorization: Bearer <token>` header). A wrong token closes the connection with code 1008.

Each text frame is one JSON message or a JSON array of messages:

```json
{"type": "heart_rate", "value": 72.5}
{"type": "gsr", "fields": {"conductance": 3.1, "raw": 512}, "timestamp": 1727600000123}
[{"type": "spo2", "value": 98}, {"type": "breathing_rate", "value": 14}]
```

- `type`: any name (`[A-Za-z0-9_.-]`). Unknown types are stored too, so the firmware can
  send new data before the server knows what to do with it.
- `value` **or** `fields`: a single value, or several named values.
- `timestamp` (optional): ISO 8601 or Unix epoch in s/ms. Defaults to the time the frame arrives.
- `tags` (optional): string metadata, e.g. `{"sensor": "max30102"}`.

Invalid frames are skipped. The server answers with `{"status": "error", "detail": ...}` and keeps the connection open.

## Extending

**New processed data**: subclass `WindowedProcessor` (reads the last `window` of raw data, writes
the result to `PROCESSED`) and implement `process()`:

```python
class BreathingRateStatsProcessor(WindowedProcessor):
    name = "breathing_rate_stats"
    input_kinds = frozenset({kinds.BREATHING_RATE})
    window = timedelta(seconds=60)

    def process(self, data: list[Measurement]) -> Sequence[Measurement]: ...
```

Then add it to `default_processors()` in `app/processing/processors/__init__.py`. To fetch
data from somewhere else (e.g. combine several kinds, or read earlier processed output), or to
store results elsewhere, subclass `Processor` directly and override `fetch` / `store`.

To give the new data a nice label and unit in the interface, add it to
`frontend/src/features/measurements/kinds.ts` (it is displayed even if you don't).

**New simulated sensor**: subclass `SignalGenerator` in `app/ingestion/dummy/generators.py` and
add it to `default_generators()`.

**New kind of source** (serial port, file replay...): subclass `DataSource` and implement
`stream()`. Hand it to `IngestionService.consume()`, or list it in `Services.background_sources()`.
