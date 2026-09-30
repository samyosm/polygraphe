import statistics
from collections.abc import Sequence
from dataclasses import dataclass

from app.domain import Measurement
from app.domain.measurement import DEFAULT_FIELD


@dataclass(frozen=True, slots=True)
class Summary:
    mean: float
    min: float
    max: float
    std: float
    count: int

    def as_fields(self) -> dict[str, float | int]:
        return {
            "mean": self.mean,
            "min": self.min,
            "max": self.max,
            "std": self.std,
            "count": self.count,
        }


def numeric_values(measurements: Sequence[Measurement], field: str = DEFAULT_FIELD) -> list[float]:
    """Extract a numeric field, skipping measurements where it is missing or not a number."""
    values = []
    for m in measurements:
        value = m.fields.get(field)
        if isinstance(value, int | float) and not isinstance(value, bool):
            values.append(float(value))
    return values


def summarize(values: Sequence[float]) -> Summary:
    if not values:
        raise ValueError("cannot summarize an empty sequence")
    return Summary(
        mean=statistics.fmean(values),
        min=min(values),
        max=max(values),
        std=statistics.pstdev(values),
        count=len(values),
    )
