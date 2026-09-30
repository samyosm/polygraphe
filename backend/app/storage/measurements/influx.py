import asyncio
import json
import logging
from collections import defaultdict
from collections.abc import Collection, Iterable, Sequence
from datetime import UTC, datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.flux_table import FluxRecord
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

from app.domain import FieldValue, Measurement, Stage
from app.storage.measurements.base import MeasurementRepository

logger = logging.getLogger(__name__)

DEVICE_TAG = "device_id"
# Columns Flux adds to every record that are neither tags nor field data.
_RESERVED_COLUMNS = {"result", "table"}


class InfluxRepository(MeasurementRepository):
    """Stores each stage in its own bucket. Measurement kind -> Influx measurement name."""

    def __init__(
        self,
        url: str,
        token: str,
        org: str,
        buckets: dict[Stage, str],
    ) -> None:
        self._url, self._token, self._org = url, token, org
        self._buckets = buckets
        self._client: InfluxDBClientAsync | None = None

    async def start(self) -> None:
        await asyncio.to_thread(self._ensure_buckets)
        self._client = InfluxDBClientAsync(url=self._url, token=self._token, org=self._org)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def write(self, stage: Stage, measurements: Sequence[Measurement]) -> None:
        if not measurements:
            return
        await (
            self._require_client()
            .write_api()
            .write(
                bucket=self._buckets[stage],
                record=[_to_point(m) for m in measurements],
                write_precision=WritePrecision.NS,
            )
        )

    async def query(
        self,
        stage: Stage,
        device_id: str,
        kinds: Collection[str] | None,
        start: datetime,
        stop: datetime,
    ) -> list[Measurement]:
        if kinds is not None and not kinds:
            return []
        flux = f"""
            from(bucket: {_flux_str(self._buckets[stage])})
              |> range(start: time(v: {_flux_time(start)}), stop: time(v: {_flux_time(stop)}))
              |> filter(fn: (r) => r.{DEVICE_TAG} == {_flux_str(device_id)})
        """
        if kinds is not None:
            flux += (
                f"|> filter(fn: (r) => contains(value: r._measurement, set: {_flux_list(kinds)}))"
            )

        records = await self._require_client().query_api().query_stream(flux)
        return _group_records([r async for r in records])

    def _require_client(self) -> InfluxDBClientAsync:
        if self._client is None:
            raise RuntimeError("InfluxRepository.start() must be called before use")
        return self._client

    def _ensure_buckets(self) -> None:
        """Create missing buckets. The async client has no buckets API, hence the sync one."""
        with InfluxDBClient(url=self._url, token=self._token, org=self._org) as client:
            api = client.buckets_api()
            for name in set(self._buckets.values()):
                if api.find_bucket_by_name(name) is None:
                    logger.info("Creating InfluxDB bucket %r", name)
                    api.create_bucket(bucket_name=name, org=self._org)


def _to_point(m: Measurement) -> Point:
    point = Point(m.kind).tag(DEVICE_TAG, m.device_id).time(m.timestamp, WritePrecision.NS)
    for key, value in m.tags.items():
        point.tag(key, value)
    for key, value in m.fields.items():
        point.field(key, _normalize_field(value))
    return point


def _normalize_field(value: FieldValue) -> FieldValue:
    # Influx rejects writes whose field type differs from earlier ones (e.g. 72 then 72.5),
    # so every number is stored as a float.
    if isinstance(value, int) and not isinstance(value, bool):
        return float(value)
    return value


def _group_records(records: Iterable[FluxRecord]) -> list[Measurement]:
    """Flux returns one record per field; merge them back into measurements."""
    grouped: dict[tuple, dict[str, FieldValue]] = defaultdict(dict)
    for record in records:
        tags = tuple(
            sorted(
                (k, v)
                for k, v in record.values.items()
                if not k.startswith("_") and k not in _RESERVED_COLUMNS and k != DEVICE_TAG
            )
        )
        key = (record.get_measurement(), record.values[DEVICE_TAG], record.get_time(), tags)
        grouped[key][record.get_field()] = record.get_value()

    measurements = [
        Measurement(kind=kind, device_id=device, fields=fields, timestamp=ts, tags=dict(tags))
        for (kind, device, ts, tags), fields in grouped.items()
    ]
    return sorted(measurements, key=lambda m: m.timestamp)


def _flux_str(value: str) -> str:
    # JSON string escaping is compatible with Flux string literals.
    return json.dumps(value)


def _flux_list(values: Iterable[str]) -> str:
    return "[" + ", ".join(_flux_str(v) for v in values) + "]"


def _flux_time(value: datetime) -> str:
    return _flux_str(value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
