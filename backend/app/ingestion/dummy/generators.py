"""Synthetic signals for the dummy device. Add a generator here to simulate a new sensor."""

import math
import random
from abc import ABC, abstractmethod
from collections.abc import Mapping

from app.domain import FieldValue, kinds
from app.domain.measurement import DEFAULT_FIELD


class SignalGenerator(ABC):
    """Produces the fields of one measurement kind as a function of time."""

    kind: str

    def __init__(self, rate_hz: float, seed: int | None = None) -> None:
        if rate_hz <= 0:
            raise ValueError("rate_hz must be positive")
        self.rate_hz = rate_hz
        self._rng = random.Random(seed)

    @property
    def period_s(self) -> float:
        return 1.0 / self.rate_hz

    @abstractmethod
    def sample(self, t: float) -> Mapping[str, FieldValue]:
        """Fields of the measurement at ``t`` seconds after the start of the simulation."""


class HeartRateGenerator(SignalGenerator):
    """Heart rate (bpm) oscillating slowly around a baseline, with gaussian noise."""

    kind = kinds.HEART_RATE

    def __init__(
        self,
        baseline_bpm: float = 72.0,
        amplitude_bpm: float = 8.0,
        oscillation_period_s: float = 30.0,
        noise_bpm: float = 1.0,
        rate_hz: float = 1.0,
        seed: int | None = None,
    ) -> None:
        super().__init__(rate_hz, seed)
        self.baseline = baseline_bpm
        self.amplitude = amplitude_bpm
        self.oscillation_period_s = oscillation_period_s
        self.noise = noise_bpm

    def sample(self, t: float) -> Mapping[str, FieldValue]:
        wave = math.sin(2 * math.pi * t / self.oscillation_period_s)
        bpm = self.baseline + self.amplitude * wave + self._rng.gauss(0, self.noise)
        return {DEFAULT_FIELD: round(bpm, 2)}


class SpO2Generator(SignalGenerator):
    """Oxygen saturation (%) close to the top of the healthy range, capped at 100 %."""

    kind = kinds.SPO2

    def __init__(
        self,
        baseline_pct: float = 97.5,
        amplitude_pct: float = 1.0,
        oscillation_period_s: float = 45.0,
        noise_pct: float = 0.3,
        rate_hz: float = 1.0,
        seed: int | None = None,
    ) -> None:
        super().__init__(rate_hz, seed)
        self.baseline = baseline_pct
        self.amplitude = amplitude_pct
        self.oscillation_period_s = oscillation_period_s
        self.noise = noise_pct

    def sample(self, t: float) -> Mapping[str, FieldValue]:
        wave = math.sin(2 * math.pi * t / self.oscillation_period_s)
        pct = self.baseline + self.amplitude * wave + self._rng.gauss(0, self.noise)
        return {DEFAULT_FIELD: round(min(pct, 100.0), 2)}


def default_generators() -> list[SignalGenerator]:
    return [HeartRateGenerator(), SpO2Generator()]
