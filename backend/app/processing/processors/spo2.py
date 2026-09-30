from collections.abc import Sequence
from datetime import timedelta

from app.domain import Measurement, kinds
from app.processing.base import WindowedProcessor
from app.processing.stats import numeric_values, summarize

DESATURATION_THRESHOLD_PCT = 90.0
PLAUSIBLE_PCT = (50.0, 100.0)


class SpO2StatsProcessor(WindowedProcessor):
    """Summary statistics of SpO2 over a sliding window, with a desaturation flag."""

    name = "spo2_stats"
    input_kinds = frozenset({kinds.SPO2})
    interval = timedelta(seconds=5)
    window = timedelta(seconds=30)

    def process(self, data: list[Measurement]) -> Sequence[Measurement]:
        low, high = PLAUSIBLE_PCT
        values = [v for v in numeric_values(data) if low <= v <= high]
        if not values:
            return []
        summary = summarize(values)
        latest = data[-1]
        return [
            Measurement(
                kind=kinds.SPO2_STATS,
                device_id=latest.device_id,
                fields={
                    **summary.as_fields(),
                    "desaturation": summary.min < DESATURATION_THRESHOLD_PCT,
                },
                timestamp=latest.timestamp,
            )
        ]
