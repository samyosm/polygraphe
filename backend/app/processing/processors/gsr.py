import statistics
from collections.abc import Sequence
from datetime import timedelta

from app.domain import Measurement, kinds
from app.processing.base import WindowedProcessor

CONDUCTANCE_FIELD = "conductance"
# Fewer samples than this and there is no baseline worth comparing to yet.
MIN_SAMPLES = 10


class GsrActivityProcessor(WindowedProcessor):
    """Makes skin conductance readable: what matters is how it moves, not its absolute value.

    Conductance drifts slowly (the *tonic* level, which differs from person to person and
    from one placement of the electrodes to the next) and bursts above it when the person is
    aroused (the *phasic* response). Every second this produces, from the last ``window``:

    - ``gsr_level``: ``level`` (mean of the last ``smoothing``, µS, noise removed) and
      ``baseline`` (median of the window, µS, the slow drift);
    - ``gsr_variation``: ``change`` = ``level - baseline`` (µS), which is about 0 at rest
      and rises during a response, and ``relative`` the same in % of the baseline.
    """

    name = "gsr_activity"
    input_kinds = frozenset({kinds.GSR})
    interval = timedelta(seconds=1)
    window = timedelta(seconds=60)
    smoothing = timedelta(seconds=2)

    def process(self, data: list[Measurement]) -> Sequence[Measurement]:
        samples = [
            (m.timestamp, float(v))
            for m in data
            if isinstance(v := m.fields.get(CONDUCTANCE_FIELD), int | float)
            and not isinstance(v, bool)
        ]
        if len(samples) < MIN_SAMPLES:
            return []

        latest = samples[-1][0]
        recent = [v for t, v in samples if latest - t <= self.smoothing]
        level = statistics.fmean(recent)
        baseline = statistics.median(v for _, v in samples)
        change = level - baseline
        device_id = data[-1].device_id
        return [
            Measurement(
                kind=kinds.GSR_LEVEL,
                device_id=device_id,
                fields={"level": level, "baseline": baseline},
                timestamp=latest,
            ),
            Measurement(
                kind=kinds.GSR_VARIATION,
                device_id=device_id,
                fields={
                    "change": change,
                    "relative": 100 * change / baseline if baseline > 0 else 0.0,
                },
                timestamp=latest,
            ),
        ]
