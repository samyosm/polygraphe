from collections.abc import Sequence
from datetime import timedelta

from app.domain import Measurement, kinds
from app.processing.base import WindowedProcessor
from app.processing.stats import numeric_values, summarize

# Outside of this range the sensor is almost certainly misreading (finger moved, etc.).
PLAUSIBLE_BPM = (30.0, 220.0)


class HeartRateStatsProcessor(WindowedProcessor):
    """Summary statistics of the heart rate over a sliding window, outliers removed."""

    name = "heart_rate_stats"
    input_kinds = frozenset({kinds.HEART_RATE})
    interval = timedelta(seconds=5)
    window = timedelta(seconds=30)

    def process(self, data: list[Measurement]) -> Sequence[Measurement]:
        low, high = PLAUSIBLE_BPM
        values = [v for v in numeric_values(data) if low <= v <= high]
        if not values:
            return []
        summary = summarize(values)
        latest = data[-1]
        return [
            Measurement(
                kind=kinds.HEART_RATE_STATS,
                device_id=latest.device_id,
                fields={**summary.as_fields(), "rejected": len(data) - len(values)},
                timestamp=latest.timestamp,
            )
        ]
